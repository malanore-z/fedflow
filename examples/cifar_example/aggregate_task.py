import os

import pandas as pd
import torch
import torch.nn as nn
from fedflow import Task
from fedflow.utils.trainer import SupervisedTrainer

from cifar_dataset import CifarDataset
from cifar_net import CifarNet


class AggregateTask(Task):

    def __init__(self, sample_dir, tasks):
        super(AggregateTask, self).__init__()
        self.sample_dir = sample_dir
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
        model = CifarNet()
        criterion = nn.CrossEntropyLoss()

        trainer = SupervisedTrainer(model, None, criterion, device=device)

        all_correct, all_total = 0, 0

        for i in range(10):
            sample_path = os.path.join(self.sample_dir, "sample-%d.csv" % i)
            df = pd.read_csv(sample_path, header=None)
            data = df.values.tolist()
            dataset = CifarDataset(data)
            loss, correct, total = trainer.test("aggregate.pth", dataset)

            ret[str(i)] = "%.2f%%(%d/%d)" % (100 * correct / total, correct, total)

            all_correct += correct
            all_total += total

        ret["ALL"] = "%.2f%%(%d/%d)" % (100 * all_correct / all_total, all_correct, all_total)

        self.set_item("acc", all_correct / all_total)

        return ret
