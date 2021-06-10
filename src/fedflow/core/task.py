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

    UNKNOWN = 0
    INIT = 1
    AVAILABLE = 2
    LOADING = 3
    WAITING = 4
    TRAINING = 5
    FINISHED = 6
    EXITED = 7
    EXCEPTION = 8
    INTERRUPT = 9


class Task(object):
    """
    """

    main_logger = logging.getLogger("fedflow.task.main")
    sub_logger = logging.getLogger("fedflow.task.sub")

    def __init__(self, task_id: Union[int, str] = None, *,
                 estimate_memory: Union[int, str] = None,
                 estimate_cuda_memory: Union[int, str] = None,
                 device=None):
        """

        :param task_id:
        :param estimate_memory:
        :param estimate_cuda_memory:
        :param device:
        """
        super(Task, self).__init__()
        self.task_id = task_id if task_id is not None else str(uuid.uuid4())
        self.estimate_memory = estimate_memory
        self.estimate_cuda_memory = estimate_cuda_memory
        self.device = device
        self.load_numbers = 0
        self.train_numbers = 0

        self.workdir = None
        self.load_time = -1
        self.train_time = -1

        self.__process = None
        self.__pipe = None
        self.__mq = None
        self.__status = TaskStatus.INIT

    @property
    def status(self) -> TaskStatus:
        return self.__status

    @status.setter
    def status(self, value: Union[int, str, TaskStatus]) -> None:
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

    # ======================================================================
    # ------------------------ main process methods ------------------------
    # --- The following methods will only be used in the main process.   ---
    # ======================================================================

    def start(self) -> None:
        self.main_logger.info("{%s} start.", self.task_id)
        self.workdir = os.path.join(os.curdir, str(self.task_id))
        self.workdir = os.path.abspath(self.workdir)
        pipe = multiprocessing.Pipe()
        self.__pipe = pipe[0]
        self.__process = multiprocessing.Process(target=self.run, args=(pipe[1], MessageListener.mq()))
        self.__process.start()

    def start_load(self) -> None:
        self.load_numbers += 1
        self.main_logger.info("{%s} start load. retry time: %d", self.task_id, self.load_numbers)
        msg = Message(source="", cmd="LOAD", data={})
        self.__pipe.send(msg)

    def start_train(self, device: str) -> None:
        self.train_numbers += 1
        self.main_logger.info("{%s} start train. retry time: %d", self.task_id, self.train_numbers)
        msg = Message(source="", cmd="TRAIN", data={
            "device": device
        })
        self.__pipe.send(msg)

    def exit(self) -> None:
        if self.__pipe is None or self.__pipe.closed:
            self.main_logger.warning("{%s} Try to exit a closed process.", self.task_id)
            return
        msg = Message(source="", cmd="EXIT", data={})
        self.__pipe.send(msg)
        self.__pipe.close()
        self.main_logger.info("{%s} exit.", self.task_id)

    def is_alive(self):
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
        self.workdir = os.path.join(os.curdir, str(self.task_id))
        self.workdir = os.path.abspath(self.workdir)
        os.makedirs(self.workdir, exist_ok=True)
        os.chdir(self.workdir)
        self.__listen()

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
    def train(self) -> dict:
        """
        User muest overwrite this method in subclass.
        When implement subclass, user should put all computer action(such as train or predict) in this method.
        In this method, self.device is usable, user can load data to specify cuda by use self.device field.
        :return:
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
            data = self.train()
            self.train_time = int(1000 * (time.time() - start_time))
            if type(data) != dict:
                data = {}
            data["load_time"] = self.load_time
            data["train_time"] = self.train_time
            self.__update_status(TaskStatus.FINISHED, data)
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
