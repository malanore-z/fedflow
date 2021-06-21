import os
import random
from pathlib import PurePosixPath

import pandas as pd
from fedflow import Task

from cifar_conf import CIFAR_ROOT


class SplitTask(Task):

    def __init__(self, nsamples=10):
        super(SplitTask, self).__init__()
        self.nsamples = nsamples
        self.samples = [[] for _ in range(self.nsamples)]

    def load(self) -> None:
        for i in range(10):
            img_names = os.listdir(PurePosixPath(CIFAR_ROOT, str(i)).as_posix())
            data = [(PurePosixPath(str(i), img_name).as_posix(), i) for img_name in img_names]
            random.shuffle(data)
            number = len(img_names) // self.nsamples
            for j in range(self.nsamples):
                self.samples[j].extend(data[number * j: number * (j + 1)])

        for i in range(self.nsamples):
            df = pd.DataFrame(self.samples[i])
            df.to_csv("sample-%d.csv" % i, header=False, index=False)

    def train(self, device: str) -> dict:
        # Nothing to do
        pass


if __name__ == "__main__":
    task = SplitTask()
    task.load()
