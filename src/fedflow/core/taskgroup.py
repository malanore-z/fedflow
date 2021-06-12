"""
TaskGroup
==========
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

    global_ids = set()

    def __init__(self, group_name: int = None, *,
                 estimate_memory: Union[int, str] = None,
                 estimate_cuda_memory: Union[int, str] = None,
                 device=None):
        """

        :param group_name:
        :param estimate_memory:
        :param estimate_cuda_memory:
        :param device:
        """
        super(TaskGroup, self).__init__()
        self.index = -1
        self.__group_name = group_name
        self.estimate_memory = estimate_memory
        self.estimate_cuda_memory = estimate_cuda_memory
        self.device = device
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
    def group_name(self):
        """
        only used for group directory name
        :return:
        """
        if self.__group_name is not None:
            return self.__group_name
        return "group-%d" % self.index

    def add_task(self, task: Task):
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
        :param task_id:
        :return:
        """
        for k, v in self.tasks.items():
            task = v.get(task_id)
            if task is not None:
                return v.get(task_id)
        return None

    def move_task(self, task_id: Union[int, str], _from: TaskStatus, _to: TaskStatus):
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

    def report_finish(self, task_id: Union[int, str], data=None):
        self.success_number += 1
        if data is None:
            data = {}
        train_acc = data.pop("train_acc") if "train_acc" in data else -1
        val_acc = data.pop("val_acc") if "val_acc" in data else -1
        load_time = data.pop("load_time") if "load_time" in data else -1
        train_time = data.pop("train_time") if "train_time" in data else -1
        res = {
            "type": "success",
            "data": {
                "train_acc": "%.2f%%" % (100 * train_acc) if train_acc != -1 else "-",
                "val_acc": "%.2f%%" % (100 * val_acc) if val_acc != -1 else "-",
                "data": json.dumps(data),
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

    def report_exception(self, task_id: Union[int, str], stage: str, message: str):
        self.failed_number += 1
        res = {
            "type": "fail",
            "data": {
                "stage": stage,
                "message": message
            }
        }
        self.result[task_id] = res

    def finished(self):
        return self.success_number + self.failed_number >= self.task_number

    def numbers(self):
        waiting_number = len(self.tasks[TaskStatus.AVAILABLE]) \
                         + len(self.tasks[TaskStatus.LOADING]) \
                         + len(self.tasks[TaskStatus.WAITING])
        training_number = len(self.tasks[TaskStatus.TRAINING])
        process_number = waiting_number + training_number
        return process_number, waiting_number, training_number

    def retrieve_task(self, status):
        tasks = self.tasks[status]
        keys = list(tasks.keys())
        if len(keys) > 0:
            idx = random.randint(0, len(keys) - 1)
            return tasks[keys[idx]]
        return None
