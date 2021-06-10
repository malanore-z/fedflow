import os

import torch.nn as nn
import torch.optim as optim
from torchvision.datasets import mnist
from torchvision.transforms import transforms
from fedflow import Task
from fedflow.utils.trainer import SupervisedTrainer

from lenet5 import Net


class TrainTask(Task):

    def __init__(self, taskid, pre_aggregate_task=None):
        super(TrainTask, self).__init__(taskid)
        self.pre_aggregate_task = pre_aggregate_task

    def load(self) -> None:
        self.mnist_dataset = mnist.MNIST(root=os.path.join(os.path.expanduser("~"), "datasets"),
                                         download=True,
                                         train=True,
                                         transform=transforms.Compose([
                                             transforms.ToTensor(),
                                             transforms.Normalize((0.13066062,), (0.30810776,))
                                         ]))
        self.mnist_model = Net()
        self.mnist_optim = optim.SGD(self.mnist_model.parameters(), lr=0.1)
        self.criterion = nn.CrossEntropyLoss()

    def train(self) -> None:
        if self.pre_aggregate_task is not None:
            init_model_path = os.path.join(self.pre_aggregate_task.workdir, "parameter.pth")
        else:
            init_model_path = None
        trainer = SupervisedTrainer(self.mnist_model, self.mnist_optim, self.criterion, epoch=40, device=self.device,
                                    init_model_path=init_model_path, console_out="console.out")
        trainer.mount_dataset(self.mnist_dataset, batch_size=128)
        return trainer.train()