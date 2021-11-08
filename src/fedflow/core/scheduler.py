"""
Schedule core
==============

The core of fedflow schedule.

``GroupScheduler`` is responsible for the parallel operation of scheduling tasks.
Generally, user should not use GroupScheduler directly.
"""

__all__ = [
    "GroupScheduler"
]

import logging
import time
from typing import Union

import ngpuinfo
import psutil
from ngpuinfo import NGPUInfo

from fedflow.config import Config
from fedflow.core.message import MessageListener, Handler
from fedflow.core.task import Task, TaskStatus
from fedflow.core.taskgroup import TaskGroup
from fedflow.mail import Mail
from fedflow.units import ByteUnits


class TaskHandler(Handler):
    """
    The handler of task process message.
    It should be registered as default handler of MessageListener before every schedule round.
    """

    main_logger = logging.getLogger("fedflow.task.main")

    def __init__(self, group: TaskGroup):
        """
        Construct a handler instance for specify group.

        :param group: the task group in scheduling.
        """
        super(TaskHandler, self).__init__()
        self.group = group

    def handle(self, source: str, cmd: str, data: dict) -> None:
        """
        handle task message.

        :param source: the task id
        :param cmd: the task action need be handled, in current version, the value is always ``update_status``
        :param data: the payload data.
        :return:
        """
        task = self.group.get_task(source)
        if cmd == "update_status":
            status = data.pop("status")
            self.main_logger.info("{%s} receive update status{%s} signal", task.task_id, status.name)
            self.handle_status(task, status, data)
        elif cmd == "set_result":
            task.result = data.copy()
        elif cmd == "set_item":
            task.items[data["key"]] = data["value"]

    def handle_status(self, task: Task, status: TaskStatus, data: dict) -> None:
        """
        handle the status update of task.

        :param task: the task which need update status.
        :param status: the target status.
        :param data: some extra data.
        :return:
        """
        if status == TaskStatus.EXCEPTION:
            message = data["message"]
            stage = data["stage"]
            self.group.report_exception(task.task_id, stage, message)
            task.exit()
            self.group.move_task(task.task_id, task.status, TaskStatus.EXCEPTION)
        elif status == TaskStatus.INTERRUPT:
            interrupt_from = data["stage"]
            self.__interrupt(task, interrupt_from)
        elif status == TaskStatus.FINISHED:
            task.exit()
            self.group.move_task(task.task_id, task.status, TaskStatus.EXITED)
            self.group.report_finish(task.task_id, data)
        else:
            self.group.move_task(task.task_id, task.status, status)

    def __interrupt(self, task: Task, interrupt_from: str) -> None:
        """
        When there is insufficient memory(or cuda memory) during the scheduling process, the task will be interrupt and
        the status of task is set to ``TaskStatus.INTERRUPT``.

        If interrupt occurs in ``load`` stage, the task process will be killed, and the status is set to
        ``TaskStatus.AVAILABLE``. Then, the task is added to available task queue, and waiting for the next schedule.

        If interrupt occurs in ``train`` stage, the task process will be reserved, and the status is set to
        ``TaskStatus.WAITING``. Then, the task is added to waiting task queue, and waiting for the next scheduler.

        The exception is if the maximum number of retries(``load`` and ``train`` stage are count separately) is reached,
        the status of task is set to ``TaskStatus.EXCEPTION``, and the task process will be killed.

        :param task: the task which interrupted.
        :param interrupt_from: the stage occurs OOM(or cuda OOM), its value only can be 'load' or 'train'
        :return:
        """
        if interrupt_from == "LOAD":
            if task.load_numbers < Config.get_property("scheduler.load-nretry"):
                task.exit()
                self.group.move_task(task.task_id, task.status, TaskStatus.AVAILABLE)
            else:
                task.exit()
                self.group.report_exception(task.task_id, "load", "LoadNumbersExceed")
                self.group.move_task(task.task_id, task.status, TaskStatus.EXCEPTION)
        else:
            if task.train_numbers < Config.get_property("scheduler.train-nretry"):
                self.group.move_task(task.task_id, task.status, TaskStatus.WAITING)
            else:
                task.exit()
                self.group.report_exception(task.task_id, "train", "TrainNumbersExceed")
                self.group.move_task(task.task_id, task.status, TaskStatus.EXCEPTION)


class GroupScheduler(object):
    """
    The scheduler of ``TaskGroup``.
    """

    logger = logging.getLogger("fedflow.scheduler")

    @classmethod
    def schedule(cls, group: TaskGroup) -> None:
        """
        The entry of schedule.

        This method is blocked.

        :param group: the task group waiting for scheduling.
        :return:
        """
        cls.logger.info("schedule group #%s", group.index)
        MessageListener.register_default_handler(TaskHandler(group))

        schedule_round = 1
        while not group.finished():
            process_number, waiting_number, training_number = group.numbers()
            cls.logger.info("schedule round #%d{waiting: %d, training: %d, process: %d}",
                            schedule_round, waiting_number, training_number, process_number)
            schedule_round += 1

            max_process = Config.get_property("scheduler.max-process")
            if process_number < max_process or max_process == 0:
                if cls.cpu_free():
                    # schedule load
                    max_waiting = Config.get_property("scheduler.max-waiting")
                    if waiting_number < max_waiting or max_waiting == 0:
                        # start init task
                        task: Task = group.retrieve_task(TaskStatus.INIT)
                        if task is not None:
                            cls.logger.info("task{%s} start", task.task_id)
                            task.start()
                            time.sleep(3)
                        else:
                            cls.logger.debug("no init task exists.")

                        # start available task
                        task: Task = group.retrieve_task(TaskStatus.AVAILABLE)
                        if task is not None:
                            require_memory = task.estimate_memory
                            if require_memory is None:
                                require_memory = group.estimate_memory
                            if cls.memory_free(require_memory):
                                cls.logger.info("task{%s} start load", task.task_id)
                                task.start_load()
                            else:
                                cls.logger.warning("memory utilization is too high.")
                        else:
                            cls.logger.debug("no available task exists.")
                    else:
                        cls.logger.info("the maximum number of waiting has been reached.")

                    # schedule train
                    task: Task = group.retrieve_task(TaskStatus.WAITING)
                    if task is not None:
                        require_cuda_memory = task.estimate_cuda_memory
                        if require_cuda_memory is None:
                            require_cuda_memory = group.estimate_cuda_memory
                        device_id = cls.assign_cuda(require_cuda_memory, task.device)
                        if device_id >= 0:
                            device = "cuda:%d" % device_id
                            cls.logger.info("task{%s} start train in %s", task.task_id, device)
                            task.start_train(device)
                        else:
                            cls.logger.warning("GPU utilization is too high.")
                    else:
                        cls.logger.info("no waiting task exists.")

                else:
                    cls.logger.warning("CPU utilization is too high.")

            else:
                cls.logger.info("the maximum number of processes has been reached.")

            cls.logger.info("sleeping...")
            time.sleep(Config.get_property("scheduler.interval"))

        # send task group report
        Mail.send_group_result(group.group_name, group.result)

    @classmethod
    def cpu_free(cls) -> bool:
        """
        check cpu utilization.

        :return: a bool value.
        """
        cpu_precent = psutil.cpu_percent()
        utilization_limit = Config.get_property("utilization-limit.cpu")
        cls.logger.debug("CPU utilization: %.2f%%", cpu_precent)
        return cpu_precent < 100 * utilization_limit

    @classmethod
    def memory_free(cls, require_memory: Union[int, str] = None) -> bool:
        """
        check memory utilization

        :param require_memory: the memory current task required. the type of ``require_memory`` can be int(the unit is
            Byte) or str(number + unit, for example, '123KB', '456 MB', '789MiB').
        :return: a bool value
        """
        if require_memory is None:
            require_memory = Config.get_property("scheduler.default-memory")
        require_memory = cls.parse_memory_value(require_memory)

        mem = psutil.virtual_memory()
        total = mem.total
        available = mem.available
        cls.logger.debug("memory utilization: %.2f%%{available: %.3fGiB, total: %.3fGiB}",
                         100 * (total - available) / total,
                         ByteUnits.convert(ByteUnits.iB, ByteUnits.GiB, available),
                         ByteUnits.convert(ByteUnits.iB, ByteUnits.GiB, total))
        available = mem.available - require_memory

        utilization_limit = Config.get_property("utilization-limit.memory")
        if available < 0 or available / total < 1 - utilization_limit:
            return False

        remain_limit = Config.get_property("remain-limit.memory")
        remain_limit = cls.parse_memory_value(remain_limit)
        if available < remain_limit:
            return False

        return True

    @classmethod
    def assign_cuda(cls, require_cuda_memory=None, device: str = None):
        """
        assign a cuda device.

        :param require_cuda_memory: the cuda memory current task required.
        :param device: specify a device, then other device will be ignored.
        :return: An integer represents the cuda id
        """
        if require_cuda_memory is None:
            require_cuda_memory = Config.get_property("scheduler.default-cuda-memory")
        require_cuda_memory = cls.parse_memory_value(require_cuda_memory)

        gpus = NGPUInfo.list_gpus()
        if device is not None:
            try:
                device = device.replace("cuda:", "")
                device_id = int(device)
                gpus = [gpus[device_id], ]
            except:
                pass

        for g in gpus:
            gpu: ngpuinfo.NGPU = g
            total = gpu.mem_total()
            available = gpu.mem_free()
            cls.logger.debug("cuda:%d memory utilization: %.2f%%{available: %.3fGiB, total: %.3fGiB}",
                             gpu.id, 100 * (total - available) / total,
                             ByteUnits.convert(ByteUnits.iB, ByteUnits.GiB, available),
                             ByteUnits.convert(ByteUnits.iB, ByteUnits.GiB, total))
            available = gpu.mem_free() - require_cuda_memory

            utilization_limit = Config.get_property("utilization-limit.cuda-memory")
            if available < 0 or available / total < 1 - utilization_limit:
                continue

            remain_limit = Config.get_property("remain-limit.cuda-memory")
            remain_limit = cls.parse_memory_value(remain_limit)
            if available < remain_limit:
                continue

            cls.logger.debug("select cuda:%d", gpu.id)
            return gpu.id

        cls.logger.debug("no free gpu.")
        return -1

    @classmethod
    def parse_memory_value(cls, value):
        if type(value) == str:
            v, u = ByteUnits.parse(value)
            value_int = ByteUnits.convert(u, ByteUnits.B, v)
            return value_int
        elif type(value) == int:
            return value
        else:
            raise ValueError("memory value only supports int or str")
