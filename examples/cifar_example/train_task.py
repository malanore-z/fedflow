from pathlib import PurePosixPath

import pandas as pd
import torch.nn as nn
from fedflow import Task
from fedflow.utils.trainer import SupervisedTrainer
from torch.optim import SGD
from torch.optim.lr_scheduler import LambdaLR

from cifar_dataset import CifarDataset
from lenet5 import LeNet5


class TrainTask(Task):

    def __init__(self, task_id, split_task: Task, aggregate_task: Task):
        super(TrainTask, self).__init__(task_id=str(task_id))
        self.split_task = split_task
        self.aggregate_task = aggregate_task

    def load(self) -> None:
        self.model = LeNet5()
        self.optimizer = SGD(self.model.parameters(), lr=0.1)
        self.lr_scheduler = LambdaLR(self.optimizer, lambda last_epoch: 0.99 ** last_epoch if last_epoch > 0 else 1)
        self.criterion = nn.CrossEntropyLoss()
        # Load dataset
        sample_path = PurePosixPath(self.split_task.workdir, "sample-%s.csv" % self.task_id).as_posix()
        df = pd.read_csv(sample_path, header=False)
        data = df.values.tolist()
        self.dataset = CifarDataset(data)

    def train(self, device: str) -> dict:
        if self.aggregate_task is not None:
            pre_model_path = PurePosixPath(self.aggregate_task.workdir, "aggregate.pth").as_posix()
        else:
            pre_model_path = None
        self.trainer = SupervisedTrainer(self.model, self.optimizer, self.criterion, self.lr_scheduler,
                                         epoch=100,
                                         device=device,
                                         init_model_path=pre_model_path)
        self.trainer.mount_dataset(self.dataset)
        return self.trainer.train()
