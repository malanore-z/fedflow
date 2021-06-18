开始使用
==============

安装
**********

``pip instal fedflow==0.2.0``

快速开始
************

1. 定义任务

.. code:: python

    from fedflow import Task
    import time

    class MyTask(Task):

        def load(self) -> None:
            for i in range(10):
                time.sleep(1)
                print("[Load] Task %s loading %d%%." % (self.task_id, 10 * (i + 1)))

        def train(self, device: str) -> dict:
            for i in range(20):
                time.sleep(1)
                print("[Train] Task %s training %d%%." % (self.task_id, 5 * (i + 1)))
            return {}

用户可以通过继承 ``Task`` 的形式很方便的定义任务。

在简单场景下，用户只需要重写 ``Task`` 的 ``load`` 和 ``train`` 方法，通常，用户需要在 ``train`` 方法中返回一个 **可以序列化的dict** ,
这个 ``dict`` 中的数据将会用于生成训练报告。

2. 创建任务组

在Fedflow中，任务的执行顺序是未知的，所以如果你需要让任务保持有序的话，需要创建一个任务组。任务组的执行顺序是严格有序的，按照它们被添加到流中的顺序,
而每个任务组内的任务是无序的。

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


在上面的代码中， ``group_1`` 将会被先执行， 但是 ``group_1`` 中的任务的执行顺序是随机的， 在所有的任务被执行完后, ``group_2`` 的任务将会被执行。

3. Start

当所有任务组都被添加到流中之后， 可以开始启动Fedflow， 这只需要一行代码。

.. code:: python

    Fedflow.start()
