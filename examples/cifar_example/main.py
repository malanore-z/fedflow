
from fedflow import FedFlow, TaskGroup

from split_task import SplitTask
from train_task import TrainTask
from aggregate_task import AggregateTask


if __name__ == "__main__":
    split_group = TaskGroup()
    split_task = SplitTask()
    split_group.add_task(split_task)
    FedFlow.add_group(split_group)

    pre_aggregate_task = None
    for i in range(5):
        train_group = TaskGroup()
        train_tasks = [TrainTask(i, split_task, pre_aggregate_task) for i in range(10)]
        for task in train_tasks:
            train_group.add_task(task)
        FedFlow.add_group(train_group)

        aggregate_group = TaskGroup()
        aggregate_task = AggregateTask(split_task, train_tasks)
        aggregate_group.add_task(aggregate_task)
        FedFlow.add_group(aggregate_group)

        pre_aggregate_task = aggregate_task

    FedFlow.start()
