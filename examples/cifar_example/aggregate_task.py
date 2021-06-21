import os

import pandas as pd
import torch
import torch.nn as nn
from fedflow import Task
from fedflow.utils.trainer import SupervisedTrainer

from cifar_dataset import CifarDataset
from lenet5 import LeNet5


class AggregateTask(Task):

    def __init__(self, split_task, tasks):
        super(AggregateTask, self).__init__()
        self.split_task = split_task
        self.tasks = tasks
        self.parameters = []

    def load(self) -> None:
        # Nothing to do
        pass

    def train(self, device) -> dict:
        for t in self.tasks:
            task: Task = t
            path = os.path.join(task.workdir, "parameter.pth")
            self.parameters.append(torch.load(path, map_location=device))

        avg_parameter = self.parameters[0]
        for key in avg_parameter.keys():
            for i in range(1, len(self.parameters)):
                avg_parameter[key] += self.parameters[i][key]
            avg_parameter[key] = torch.div(avg_parameter[key], len(self.parameters))
        torch.save(avg_parameter, "aggregate.pth")

        return self.test(device=device)

    def test(self, device) -> dict:
        ret = {}
        model = LeNet5()
        criterion = nn.CrossEntropyLoss()

        trainer = SupervisedTrainer(model, None, criterion, device=device)

        all_correct, all_total = 0, 0

        for i in range(10):
            sample_path = os.path.join(self.split_task.workdir, "sample-%d.csv" % i)
            df = pd.read_csv(sample_path, header=None)
            data = df.values.tolist()
            dataset = CifarDataset(data)
            loss, correct, total = trainer.test(dataset)

            ret[str(i)] = {
                "correct": correct,
                "total": total,
                "acc": correct / total
            }

            all_correct += correct
            all_total += total

        ret["ALL"] = {
            "correct": all_correct,
            "total": all_total,
            "acc": all_correct / all_total
        }

        return ret
