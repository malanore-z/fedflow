"""
TaskGroup
==========

All tasks in one group will executed disorderly.
"""

__all__ = [
    "TaskGroup"
]

import json
import random
from typing import Union

from fedflow.config import Config
from fedflow.core.task import Task, TaskStatus


class TaskGroup(object):

    """
    Generally, tasks in one group should be similar, it means all tasks is instance of the same class.

    Of course, this is not mandatory, you just need to ensure that there are no dependencies between tasks.
    """

    global_ids = set()

    def __init__(self, group_name: str = None, *,
                 estimate_memory: Union[int, str] = None,
                 estimate_cuda_memory: Union[int, str] = None,
                 device=None):
        """
        Construct a task group.

        :param group_name: the group name, it only used for create group directory and display in report.
        :param estimate_memory: maximum memory expected to be used for every task in this group.
        :param estimate_cuda_memory: maximum cuda memory expected to be used for every task in this group.
        :param device: specify device the tasks in this group used, if it's None, the device will be decided by
        scheduler.
        """
        super(TaskGroup, self).__init__()
        self.index = -1
        self.__group_name = group_name
        self.estimate_memory = estimate_memory
        self.estimate_cuda_memory = estimate_cuda_memory
        self.__device = device
        self.auto_adjust_memory = self.estimate_memory is None
        self.auto_adjust_cuda_memory = self.estimate_cuda_memory is None
        if not Config.get_property("scheduler.auto-adjust"):
            self.auto_adjust_memory = False
            self.auto_adjust_cuda_memory = False

        self.task_ids = set()
        self.tasks = {}
        for ts in TaskStatus.__members__.values():
            self.tasks[ts] = {}

        self.task_number = 0
        self.success_number = 0
        self.failed_number = 0

        self.result = {}

        self.workdir = None

    @property
    def device(self) -> str:
        return self.__device

    @property
    def group_name(self) -> str:
        """
        only used for group directory name.

        :return: a string represent group name.
        """
        if self.__group_name is not None:
            return self.__group_name
        return "group-%d" % self.index

    def add_task(self, task: Task) -> None:
        """
        Add a task to this group.

        :param task: the task to be added to this group
        :return:
        """
        if task.device is None:
            task.device = self.device

        if not Config.get_property("task.allow-duplicate-id") and task.task_id in TaskGroup.global_ids:
            raise ValueError("Duplicate id[%s] in global." % str(task.task_id))
        TaskGroup.global_ids.add(task.task_id)
        if task.task_id in self.task_ids:
            raise ValueError("Duplicate id[%s] in group." % str(task.task_id))
        self.task_ids.add(task.task_id)

        self.tasks[task.status][task.task_id] = task
        self.task_number += 1

    def get_task(self, task_id: Union[int, str]) -> Union[Task, None]:
        """
        Get specify task in group

        :param task_id: the unique task id.
        :return: an instance of ``Task`` or None if not found.
        """
        for k, v in self.tasks.items():
            task = v.get(task_id)
            if task is not None:
                return v.get(task_id)
        return None

    def move_task(self, task_id: Union[int, str], _from: TaskStatus, _to: TaskStatus) -> None:
        """
        Move task from one container to other container.
        An exception will be threw if task not exists in _from container.
        This method will update the status of task after successfully moved.

        :param task_id: the id of task
        :param _from: the status move from
        :param _to: the status move to
        :return:
        """
        if task_id not in self.tasks[_from]:
            raise ValueError("task id %s not exists in %s status" % (str(task_id), _from.name))
        task = self.tasks[_from].pop(task_id)
        self.tasks[_to][task_id] = task
        task.status = _to

    def report_finish(self, task_id: Union[int, str], data=None) -> None:
        """
        report a task finished.

        :param task_id: the finished task id
        :param data: extra report data
        :return:
        """
        self.success_number += 1
        if data is None:
            data = {}
        load_time = data["load_time"] if "load_time" in data else -1
        train_time = data["train_time"] if "train_time" in data else -1
        real_data = data["data"] if "data" in data else {}
        train_acc = real_data.pop("train_acc") if "train_acc" in data else -1
        val_acc = real_data.pop("val_acc") if "val_acc" in data else -1
        res = {
            "type": "success",
            "data": {
                "train_acc": "%.2f%%" % (100 * train_acc) if train_acc != -1 else "-",
                "val_acc": "%.2f%%" % (100 * val_acc) if val_acc != -1 else "-",
                "data": json.dumps(real_data),
                "load_time": self.__time_format(load_time),
                "train_time": self.__time_format(train_time)
            }
        }
        self.result[task_id] = res

    def __time_format(self, milliseconds):
        if milliseconds is None or milliseconds < 0:
            return "--:--:--.---"
        seconds = milliseconds // 1000
        milliseconds = milliseconds % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        return "%02d:%02d:%02d.%03d" % (hours, minutes, seconds, milliseconds)

    def report_exception(self, task_id: Union[int, str], stage: str, message: str) -> None:
        """
        report a task caught exception.

        :param task_id: the exception task id.
        :param stage: the stage of exception caught('load' or 'train').
        :param message: exception message
        :return:
        """
        self.failed_number += 1
        res = {
            "type": "fail",
            "data": {
                "stage": stage,
                "message": message
            }
        }
        self.result[task_id] = res

    def finished(self) -> bool:
        """
        If all tasks in this group is finished or caught exception.

        :return: a bool value
        """
        return self.success_number + self.failed_number >= self.task_number

    def numbers(self):
        """
        the task numbers of this group

        :return: a tuple ``(process_number, waiting_number, training_number)``
        """
        waiting_number = len(self.tasks[TaskStatus.AVAILABLE]) \
                         + len(self.tasks[TaskStatus.LOADING]) \
                         + len(self.tasks[TaskStatus.WAITING])
        training_number = len(self.tasks[TaskStatus.TRAINING])
        process_number = waiting_number + training_number
        return process_number, waiting_number, training_number

    def retrieve_task(self, status) -> Union[Task, None]:
        """
        randomly retrieve a task which has ``status``.

        :param status: which status task need
        :return: the task retrieved or None if not found.
        """
        tasks = self.tasks[status]
        keys = list(tasks.keys())
        if len(keys) > 0:
            idx = random.randint(0, len(keys) - 1)
            return tasks[keys[idx]]
        return None
