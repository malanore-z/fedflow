.. Fedflow documentation master file, created by
   sphinx-quickstart on Sat Jun 12 19:21:55 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Fedflow: auto-scheduler for pytorch task.
=========================================

Fedflow是一个自动并行调度pytorch任务的框架，主要用于分布式机器学习。

当用户需要在单个设备上模拟多节点环境时， 受限于单设备资源限制（CPU，内存，显存等），不能将这些任务并行运行，而如果用串行模拟多节点环境，一则耗时良久，
二则浪费了单设备的资源，通常单个任务不能占满显存等资源。

Fedflow是这样一个调度框架，用户可以一次定义所有需要的任务，并将其添加到Fedflow的任务流中，由Fedflow负责调度任务的运行。通常情况下，Fedflow会尝试
同时运行尽可能多的任务以最大化利用系统资源。

Table of Contents
------------------

.. toctree::
   :maxdepth: 4
   :caption: 开始

   start
   config
   component

.. toctree::
   :maxdepth: 4
   :caption: 示例

   mnist_example
   cifar_example

.. toctree::
   :maxdepth: 4
   :caption: API

   fedflow
   core
   mail
   utils

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
