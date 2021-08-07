"""
Fedflow entry
==============

"""

__all__ = [
    "FedFlow"
]


import os

from fedflow.config import Config
from fedflow.context import WorkDirContext
from fedflow.core.message import MessageListener
from fedflow.core.scheduler import GroupScheduler
from fedflow.core.taskgroup import TaskGroup


class FedFlow(object):

    """
    The entry class of Fedflow
    """

    groups = []

    def __init__(self):
        super(FedFlow, self).__init__()
        self.in_working = False

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self.in_working = True
        workdir = Config.get_property("workdir")
        os.makedirs(workdir, exist_ok=True)
        os.chdir(workdir)

        MessageListener.start()

    def close(self):
        MessageListener.stop()
        self.in_working = False

    def execute(self, group: TaskGroup) -> None:
        if not self.in_working:
            raise ValueError("Please use 'with Fedflow()'")
        if Config.get_property("task.directory-grouping"):
            os.makedirs(group.group_name, exist_ok=True)
            with WorkDirContext(group.group_name):
                group.workdir = os.path.abspath(".")
                GroupScheduler.schedule(group)
        else:
            GroupScheduler.schedule(group)

    @classmethod
    def add_group(cls, group: TaskGroup) -> None:
        """
        Add a task group to flow.

        :param group: an instance of ``TaskGroup``
        :return:
        """
        cls.groups.append(group)
        group.index = len(cls.groups)

    @classmethod
    def start(cls) -> None:
        """
        Start schedule tasks

        :return:
        """
        workdir = Config.get_property("workdir")
        workdir = os.path.abspath(workdir)
        os.makedirs(workdir, exist_ok=True)
        os.chdir(workdir)

        MessageListener.start()

        for g in cls.groups:
            if Config.get_property("task.directory-grouping"):
                os.makedirs(g.group_name, exist_ok=True)
                with WorkDirContext(g.group_name):
                    g.workdir = os.path.abspath(".")
                    GroupScheduler.schedule(g)
            else:
                GroupScheduler.schedule(g)

        MessageListener.stop()
