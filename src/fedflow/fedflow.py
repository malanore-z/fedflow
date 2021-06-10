import os

from fedflow.config import Config
from fedflow.context import WorkDirContext
from fedflow.core.message import MessageListener
from fedflow.core.scheduler import GroupScheduler
from fedflow.core.taskgroup import TaskGroup


class FedFlow(object):

    groups = []

    def __init__(self):
        super(FedFlow, self).__init__()

    @classmethod
    def add_group(cls, group: TaskGroup):
        cls.groups.append(group)
        group.index = len(cls.groups)

    @classmethod
    def start(cls):
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
