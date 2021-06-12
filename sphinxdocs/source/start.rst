Introduction
==============

Description
***************

auto-scheduler for pytorch task.

Install
**********

``pip instal fedflow==0.2.0b2``

Quick Start
************

1. Define your task

.. code:: python

    from fedflow import Task

    class MyTask(Task):

        def load(self) -> None:
            # Some loading actions
            # It is recommended that user keep memory usage unchanged after this function is called.
            pass

        def train(self) -> dict:
            # Some actions that use GPU
            # In this method, self.device is usable, user can load data to specify cuda by use self.device field.
            pass

Users can simply define tasks by inheriting the Task class.

In a simple scenario, user only need overwrite load and train methods, usually user should return a dict after call train
method, the dict contains data will be reported.

2. Create task group

In Fedflow, the order of task execution is unknowable, so if you want to keep tasks in order, you need create groups.
the groups are executed in the order in which they are added.

.. code:: python

    from fedflow import TaskGroup, FedFlow

    group_1 = TaskGroup()
    for i in range(10):
        group_1.add_task(MyTask(i))
    group_2 = TaskGroup()
    for i in range(10, 20):
        group_2.add_task(MyTask(i))

    FedFlow.add_group(group_1)
    FedFlow.add_group(group_2)

In the code above, group_1 will be executed first, but the order of tasks(0..9) execution is random. After all tasks in
group_1 are executed, the tasks in group_2 will be executed.

3. Start

When all groups were added to Fedflow, you can start Fedflow by only one-line code.

.. code:: python

    Fedflow.start()
