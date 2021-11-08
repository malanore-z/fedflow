# Fed Flow

## Description

auto-scheduler for parallel task.

## Install

`pip instal fedflow==0.2.0`

## Usage

```python
import os

import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torchvision.datasets import mnist
from torchvision.transforms import transforms

from fedflow import Task, TaskGroup, FedFlow
from fedflow.config import Config
from fedflow.utils.trainer.supervised_trainer import SupervisedTrainer


Config.set_property("debug", True)
Config.set_property("scheduler.interval", 2)


datasets_path = os.path.join(os.path.abspath("."), "datasets")


class Net(nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4 * 4 * 50, 500)
        self.fc2 = nn.Linear(500, 10)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        x = x.view(-1, 4 * 4 * 50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class MnistTask(Task):

    def __init__(self, id, datasets_path):
        super(MnistTask, self).__init__(task_id=id, estimate_memory="2.5GB", estimate_cuda_memory="1200MB")
        self.datasets_path = datasets_path

    def load(self):
        self.mnist_dataset = mnist.MNIST(root=self.datasets_path,
                                         download=True,
                                         train=True,
                                         transform=transforms.Compose([
                                             transforms.ToTensor(),
                                             transforms.Normalize((0.13066062,), (0.30810776,))
                                         ]))
        self.test_dataset = mnist.MNIST(root=self.datasets_path,
                                        download=True,
                                        train=False,
                                        transform=transforms.Compose([
                                             transforms.ToTensor(),
                                             transforms.Normalize((0.13066062,), (0.30810776,))
                                         ]))
        self.mnist_model = Net()
        self.mnist_optim = optim.SGD(self.mnist_model.parameters(), lr=0.01)
        self.criterion = nn.CrossEntropyLoss()

    def train(self, device) -> dict:
        self.mnist_model = self.mnist_model.to(self.device)
        trainer = SupervisedTrainer(self.mnist_model, self.mnist_optim, self.criterion, epoch=50, device=self.device,
                                    console_out="console.out")
        trainer.mount_dataset(self.mnist_dataset, self.test_dataset, batch_size=32)
        return trainer.train()


def print_result(group: TaskGroup):
    print("%2s %9s %9s" % ("ID", "train acc", " val acc "))
    for i in range(20):
        task = group.get_task(i)
        result = task.result
        print("%02d  %6.2f%%   %6.2f%%" % (i, result["train_acc"], result["val_acc"]))


if __name__ == "__main__":
    # Download mnist datasets
    mnist.MNIST(root=datasets_path, download=True)
    group = TaskGroup("mnist")
    for i in range(20):
        group.add_task(MnistTask(i, datasets_path))
    with FedFlow() as flow:
        flow.execute(group)

    print_result(group)

```

## Features
+ add subprocess tracker
+ add GPUs load balancing
+ add methods to kill specified subprocess/task
