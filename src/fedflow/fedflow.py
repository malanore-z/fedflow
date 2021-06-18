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
