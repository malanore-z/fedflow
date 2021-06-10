try:
    import fedflow
except:
    import os
    import sys
    root_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.dirname(os.path.dirname(root_dir))
    fedflow_dir = os.path.join(root_dir, "src")
    sys.path.insert(0, fedflow_dir)

from fedflow import FedFlow, TaskGroup

from download_task import DownloadTask
from train_task import TrainTask
from aggregate_task import AggregateTask


if __name__ == "__main__":
    # Download mnist datasets
    download_group = TaskGroup()
    download_group.add_task(DownloadTask())
    FedFlow.add_group(download_group)

    pre_aggregate_task = None
    for i in range(3):
        train_group = TaskGroup()
        tasks = [TrainTask(i, pre_aggregate_task) for i in range(20)]
        for t in tasks:
            train_group.add_task(t)
        FedFlow.add_group(train_group)

        aggregate_group = TaskGroup()
        aggregate_task = AggregateTask(tasks)
        aggregate_group.add_task(aggregate_task)
        FedFlow.add_group(aggregate_group)

        pre_aggregate_task = aggregate_task

    FedFlow.start()
