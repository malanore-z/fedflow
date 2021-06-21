import os

import pandas as pd
import torch.nn as nn
from fedflow import Task
from fedflow.utils.trainer import SupervisedTrainer
from torch.optim import SGD
from torch.optim.lr_scheduler import MultiStepLR

from cifar_dataset import CifarDataset
from lenet5 import LeNet5


class TrainTask(Task):

    def __init__(self, task_id, split_task: Task, aggregate_task: Task):
        super(TrainTask, self).__init__(task_id=str(task_id))
        self.split_task = split_task
        self.aggregate_task = aggregate_task

    def load(self) -> None:
        self.model = LeNet5()
        self.optimizer = SGD(self.model.parameters(), lr=0.05)
        self.lr_scheduler = MultiStepLR(self.optimizer, [10, 30, 60, 90])
        self.criterion = nn.CrossEntropyLoss()
        # Load dataset
        sample_path = os.path.join(self.split_task.workdir, "sample-%s.csv" % self.task_id)
        df = pd.read_csv(sample_path, header=None)
        data = df.values.tolist()
        self.dataset = CifarDataset(data)

    def train(self, device: str) -> dict:
        if self.aggregate_task is not None:
            pre_model_path = os.path.join(self.aggregate_task.workdir, "aggregate.pth")
        else:
            pre_model_path = None
        self.trainer = SupervisedTrainer(self.model, self.optimizer, self.criterion, self.lr_scheduler,
                                         epoch=100,
                                         device=device,
                                         init_model_path=pre_model_path,
                                         console_out="console.out")

        _, correct, total = self.trainer.test(pre_model_path, self.dataset)
        ret = {
            "init_acc": "%.2f%%(%d/%d)" % (100 * correct / total, correct, total)
        }

        self.trainer.mount_dataset(self.dataset)

        ret.update(self.trainer.train())
        return ret
