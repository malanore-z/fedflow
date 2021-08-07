"""
Task
=====

The basic class of task.

User define task by inherit the ``Task`` class and overwrite ``load`` and ``train`` methods.
"""

__all__ = [
    "Task",
    "TaskStatus"
]


import abc
import enum
import logging
import multiprocessing
import os
import threading
import time
import traceback
import uuid
from typing import Union

from fedflow.core.message import Message, MessageListener


class TaskStatus(enum.Enum):

    """
    The task status enum.
    """

    UNKNOWN = 0         #: the error status
    INIT = 1            #: construct a task instance and hasn't started scheduling
    AVAILABLE = 2       #: start task subprocess
    LOADING = 3         #: start loading
    WAITING = 4         #: loaded successfully, and waiting for training
    TRAINING = 5        #: start training
    FINISHED = 6        #: training successfully
    EXITED = 7          #: subprocess exited
    EXCEPTION = 8       #: caught some exception while running
    INTERRUPT = 9       #: caught OOM(or cuda OOM) exception while running


class Task(object):
    """
    the basic class of all user task
    """

    main_logger = logging.getLogger("fedflow.task.main")
    sub_logger = logging.getLogger("fedflow.task.sub")

    def __init__(self, task_id: Union[int, str] = None, *,
                 estimate_memory: Union[int, str] = None,
                 estimate_cuda_memory: Union[int, str] = None,
                 device=None):
        """
        Construct an instance of task

        :param task_id: task unique id, default is uuid string.
        :param estimate_memory: maximum memory expected to be used.
        :param estimate_cuda_memory: maximum cuda memory expected to be used.
        :param device: specify device the task used, if it's None, the device will be decided by scheduler.
        """
        super(Task, self).__init__()
        self.task_id = task_id if task_id is not None else str(uuid.uuid4())
        self.estimate_memory = estimate_memory
        self.estimate_cuda_memory = estimate_cuda_memory
        self.device = device
        self.load_numbers = 0
        self.train_numbers = 0

        self.__workdir = None
        self.load_time = -1
        self.train_time = -1

        self.items = {}
        self.result = {}

        self.__process = None
        self.__pipe = None
        self.__mq = None
        self.__status = TaskStatus.INIT

        self.__main_pid = os.getpid()

    @property
    def workdir(self) -> str:
        """
        The workdir of task.

        This property only can be used after task process was started.

        :return:
        """
        if self.__workdir is None:
            raise ValueError("The workdir field is not available.")
        return self.__workdir

    @property
    def status(self) -> TaskStatus:
        """
        The status of task.

        :return:
        """
        return self.__status

    @status.setter
    def status(self, value: Union[int, str, TaskStatus]) -> None:
        """
        status setter

        :param value: a int/str/TaskStatus value represents the status
        :return:
        """
        try:
            if isinstance(value, int):
                s = TaskStatus(value)
            elif isinstance(value, str):
                s = TaskStatus[value]
            elif isinstance(value, TaskStatus):
                s = value
            else:
                s = TaskStatus.UNKNOWN
        except:
            s = TaskStatus.UNKNOWN
        self.__status = s

    def get_item(self, key):
        return self.items.get(key)

    # ======================================================================
    # ------------------------ main process methods ------------------------
    # --- The following methods will only be used in the main process.   ---
    # ======================================================================

    def start(self) -> None:
        """
        Start task process
        *This method cannot be called by user.*

        :return:
        """
        self.main_logger.info("{%s} start.", self.task_id)
        self.__workdir = os.path.join(os.curdir, str(self.task_id))
        self.__workdir = os.path.abspath(self.__workdir)
        pipe = multiprocessing.Pipe()
        self.__pipe = pipe[0]
        self.__process = multiprocessing.Process(target=self.run, args=(pipe[1], MessageListener.mq()))
        self.__process.start()

    def start_load(self) -> None:
        """
        Start loading.
        *This method cannot be called by user.*

        :return:
        """
        self.load_numbers += 1
        self.main_logger.info("{%s} start load. retry time: %d", self.task_id, self.load_numbers)
        msg = Message(source="", cmd="LOAD", data={})
        self.__pipe.send(msg)

    def start_train(self, device: str) -> None:
        """
        Start training.
        *This method cannot be called by user.*

        :param device: the device this task will use.
        :return:
        """
        self.train_numbers += 1
        self.main_logger.info("{%s} start train. retry time: %d", self.task_id, self.train_numbers)
        msg = Message(source="", cmd="TRAIN", data={
            "device": device
        })
        self.__pipe.send(msg)

    def exit(self) -> None:
        """
        Exit task process.
        *This method cannot be called by user.*

        :return:
        """
        if self.__pipe is None or self.__pipe.closed:
            self.main_logger.warning("{%s} Try to exit a closed process.", self.task_id)
            return
        msg = Message(source="", cmd="EXIT", data={})
        self.__pipe.send(msg)
        self.__pipe.close()
        self.main_logger.info("{%s} exit.", self.task_id)

    def is_alive(self) -> bool:
        """
        If the task process is alive.

        :return: a bool value
        """
        return self.__process is not None and self.__process.is_alive()

    # ======================================================================
    # ------------------------- subprocess methods -------------------------
    # --- The following methods will be only be used  in the subprocess. ---
    # --- It means that  the  following method and  the above method run ---
    # --- in  different process spaces.                                  ---
    # ======================================================================

    def run(self, pipe, mq) -> None:
        """
        subprocess code entry

        :param pipe: connection pipe between main process task and subprocess task
        :param mq: connection queue between main process scheduler and subprocess tasks
        :return:
        """
        self.sub_logger.info("{%s} run.", self.task_id)
        self.__pipe = pipe
        self.__mq = mq
        self.__workdir = os.path.join(os.curdir, str(self.task_id))
        self.__workdir = os.path.abspath(self.__workdir)
        os.makedirs(self.__workdir, exist_ok=True)
        os.chdir(self.__workdir)
        self.__listen()

    def set_item(self, key, value):
        if os.getpid() == self.__main_pid:
            raise ValueError("You cannot call this method in main process.")
        self.items[key] = value
        self.__send_message("set_item", {
            "key": key,
            "value": value
        })

    def __listen(self) -> None:
        """
        listen command from main process

        :return:
        """
        self.__update_status(TaskStatus.AVAILABLE)
        while True:
            msg: Message = self.__pipe.recv()
            if msg.cmd == "EXIT":
                self.sub_logger.info("{%s} receive EXIT signal", self.task_id)
                break
            elif msg.cmd == "LOAD":
                self.sub_logger.info("{%s} receive LOAD signal", self.task_id)
                t = threading.Thread(target=self.__load)
                t.start()
            elif msg.cmd == "TRAIN":
                self.device = msg.data["device"]
                self.sub_logger.info("{%s} receive TRAIN[%s] signal", self.task_id, self.device)
                t = threading.Thread(target=self.__train)
                t.start()
        self.__pipe.close()

    @abc.abstractmethod
    def load(self) -> None:
        """
        User must overwrite this method in subclass.
        When implement subclass, user should put all loading action(such as load datasets) in this method.

        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def train(self, device: str) -> dict:
        """
        User must overwrite this method in subclass.
        When implement subclass, user should put all computer action(such as train or predict) in this method.

        :param device: the device this task will use.
        :return: a dict represent some properties used for reporting.
        """
        raise NotImplementedError()

    def __load(self):
        try:
            self.__update_status(TaskStatus.LOADING)
            start_time = time.time()
            self.load()
            self.load_time = int(1000 * (time.time() - start_time))
            self.__update_status(TaskStatus.WAITING)
            self.sub_logger.info("{%s} load successful, used %dms", self.task_id, self.load_time)
        except Exception as e:
            if type(e) == MemoryError:
                self.sub_logger.error("{%s} OOM", self.task_id)
                self.__update_status(TaskStatus.INTERRUPT, {
                    "stage": "LOAD"
                })
            else:
                self.sub_logger.error("{%s} an error occurred during loading.", self.task_id,
                                      exc_info=True, stack_info=True)
                self.__update_status(TaskStatus.EXCEPTION, {
                    "message": traceback.format_exc(),
                    "stage": "LOAD"
                })

    def __train(self):
        try:
            self.__update_status(TaskStatus.TRAINING)
            start_time = time.time()
            data = self.train(self.device)
            self.train_time = int(1000 * (time.time() - start_time))
            if type(data) != dict:
                self.sub_logger.warning("the train method returns illegal data(the data must be a dict)")
                data = {}

            self.__send_message("set_result", data)

            send_data = {
                "load_time": self.load_time,
                "train_time": self.train_time,
                "data": data
            }
            self.__update_status(TaskStatus.FINISHED, send_data)
            self.sub_logger.info("{%s} train successful, used %dms", self.task_id, self.train_time)
        except Exception as e:
            if type(e) == RuntimeError and len(e.args) > 0 and "CUDA out of memory" in e.args[0]:
                self.sub_logger.error("{%s} cuda OOM", self.task_id)
                self.__update_status(TaskStatus.INTERRUPT, {
                    "stage": "TRAIN"
                })
            else:
                self.sub_logger.error("{%s} an error occurred during training.", self.task_id,
                                      exc_info=True, stack_info=True)
                self.__update_status(TaskStatus.EXCEPTION, {
                    "message": traceback.format_exc(),
                    "stage": "TRAIN"
                })

    def __update_status(self, v, data=None):
        self.__status = v
        if data is None:
            data = {}
        data["status"] = v
        self.sub_logger.info("{%s} update status to %s", self.task_id, v.name)
        self.__send_message("update_status", data)

    def __send_message(self, cmd, data=None):
        if data is None:
            data = {}
        msg = Message(source=self.task_id, cmd=cmd, data=data)
        self.__mq.put(msg)
