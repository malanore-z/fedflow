import os

from torchvision.datasets import mnist
from torchvision.transforms import transforms

from fedflow import Task


class DownloadTask(Task):

    def load(self) -> None:
        mnist.MNIST(root=os.path.join(os.path.expanduser("~"), "datasets"),
                    download=True,
                    train=True,
                    transform=transforms.Compose([
                        transforms.ToTensor(),
                        transforms.Normalize((0.13066062,), (0.30810776,))
                    ]))

    def train(self) -> None:
        # Nothing to do
        pass
