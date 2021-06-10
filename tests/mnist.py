import fedflow_test

import os

import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torchvision.datasets import mnist
from torchvision.transforms import transforms

from fedflow import Task, TaskGroup, FedFlow
from fedflow.utils.trainer.supervised_trainer import SupervisedTrainer

abspath = os.path.abspath(".")

print("Downloading...")
mnist.MNIST(root=os.path.join(abspath, "datasets"),
            download=True,
            train=True,
            transform=transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.13066062,), (0.30810776,))
            ]))
print("Download Finished.")


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

    def __init__(self, id):
        super(MnistTask, self).__init__(task_id=id)

    def load(self):
        self.mnist_dataset = mnist.MNIST(root=os.path.join(abspath, "datasets"),
                                         download=True,
                                         train=True,
                                         transform=transforms.Compose([
                                             transforms.ToTensor(),
                                             transforms.Normalize((0.13066062,), (0.30810776,))
                                         ]))
        self.mnist_model = Net()
        self.mnist_optim = optim.Adam(self.mnist_model.parameters(), lr=0.1)
        self.criterion = nn.CrossEntropyLoss()

    def train(self):
        self.mnist_model = self.mnist_model.to(self.device)
        trainer = SupervisedTrainer(self.mnist_model, self.mnist_optim, self.criterion, epoch=20, device=self.device,
                                    console_out="console.out")
        trainer.mount_dataset(self.mnist_dataset, batch_size=32)
        trainer.train()


if __name__ == "__main__":
    for i in range(3):
        group = TaskGroup()
        for j in range(10):
            task = MnistTask(10 * i + j)
            group.add_task(task)
        FedFlow.add_group(group)

    FedFlow.start()
