import os

import torch
from fedflow import Task


class AggregateTask(Task):

    def __init__(self, tasks):
        super(AggregateTask, self).__init__()
        self.tasks = tasks
        self.parameters = []

    def load(self) -> None:
        # Nothing to do
        pass

    def train(self) -> None:
        for t in self.tasks:
            task: Task = t
            path = os.path.join(task.workdir, "parameter.pth")
            self.parameters.append(torch.load(path, map_location=self.device))

        avg_parameter = self.parameters[0]
        for key in avg_parameter.keys():
            for i in range(1, len(self.parameters)):
                avg_parameter[key] += self.parameters[i][key]
            avg_parameter[key] = torch.div(avg_parameter[key], len(self.parameters))
        torch.save(avg_parameter, "aggregate.pth")
