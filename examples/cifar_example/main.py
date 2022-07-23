try:
    import fedflow
except:
    import os
    import sys
    root_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.dirname(os.path.dirname(root_dir))
    fedflow_dir = os.path.join(root_dir, "src")
    sys.path.insert(0, fedflow_dir)

import json
import os
import shutil

import matplotlib.pyplot as plt
from fedflow import FedFlow, TaskGroup

from split_task import SplitTask
from train_task import TrainTask
from aggregate_task import AggregateTask


def remove_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


if __name__ == "__main__":
    split_task = SplitTask()
    with FedFlow() as flow:
        flow.execute_task(split_task)

    sample_dir = split_task.workdir

    pre_aggregate_group = None
    pre_aggregate_task = None
    acc_history = []
    for i in range(50):
        train_group = TaskGroup("train-%d" % (i + 1))
        if pre_aggregate_task is not None:
            train_tasks = [TrainTask(j, sample_dir, pre_aggregate_task.workdir) for j in range(10)]
        else:
            train_tasks = [TrainTask(j, sample_dir) for j in range(10)]
        for task in train_tasks:
            train_group.add_task(task)
        with FedFlow() as flow:
            flow.execute(train_group)

        if pre_aggregate_group is not None:
            remove_path(pre_aggregate_group.workdir)

        aggregate_group = TaskGroup("aggregate-%d" % (i + 1))
        aggregate_task = AggregateTask(split_task.workdir, train_tasks)
        aggregate_group.add_task(aggregate_task)
        with FedFlow() as flow:
            flow.execute(aggregate_group)

        acc_history.append(aggregate_task.get_item("acc"))

        pre_aggregate_group = aggregate_group
        pre_aggregate_task = aggregate_task

        remove_path(train_group.workdir)

    with open("history.json", "w") as f:
        f.write(json.dumps(acc_history))

    plt.figure()
    plt.plot(list(range(len(acc_history))), acc_history)
    plt.grid()
    plt.legend()

    plt.savefig("history.png")
