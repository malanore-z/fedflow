# Examples

In this page, a complete federate task(fmnist) will be defined.

The complete code is stored in the `<root>/examples/mnist_example/` directory.

## Define task

### 1. Download mnist datasets task
```python
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
```

### 2. train task
```python
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
```

### 3. aggregate task
```python
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
```

## Create groups