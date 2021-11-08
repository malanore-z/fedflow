"""
Supervised Trainer
======================

A trainer used for supervised training by pytorch.
"""

__all__ = [
    "SupervisedTrainer"
]

import os
import json
import sys
import time
from collections import namedtuple

import torch
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from torch.utils.data import random_split, DataLoader


class SupervisedTrainer(object):

    """
    A trainer used for supervised training by pytorch.

    After training of this trainer, there are 4 files will appeared in current dir:

        * history.json: the data of history(contains loss and acc of train and validate).
        * history.png: the chart of history
        * parameter.pth: the parameters of model
        * optimizer.pth: the parameters of optimizer

    """

    History = namedtuple("History", ["train_loss", "train_acc", "val_loss", "val_acc", "lr"])
    History.__doc__ = "Record history data during training"
    History.train_acc.__doc__ = "train accuracy of every epoch"
    History.val_acc.__doc__ = "validate accuracy of every epoch"
    History.train_loss.__doc__ = "train loss of every epoch"
    History.val_loss.__doc__ = "validate loss of every epoch"
    History.lr.__doc__ = "learning rate of every epoch"

    def __init__(self, model, optimizer, criterion, lr_scheduler=None, *,
                 init_model_path=None,
                 init_optim_path=None,
                 dataset=None,
                 batch_size=32,
                 epoch=50,
                 epoch_action=None,
                 checkpoint_interval=10,
                 device="cuda:0",
                 console_out=None,
                 result_dir="."):
        """
        Construct a trainer.

        :param model: an instance of ``torch.nn.Module``.
        :param optimizer: an instance of pytorch optimizer.
        :param criterion: loss function
        :param lr_scheduler: an instance of ``torch.optim.lr_scheduler._LRScheduler`` or
            ``torch.optim.lr_scheduler.ReduceLROnPlateau``
        :param init_model_path: the init model parameters path.
        :param init_optim_path: the init optimizer parameters path.
        :param dataset: the datasets used for this trainer.
        :param batch_size: the batch size
        :param epoch: the epoch
        :param epoch_action: when every epoch finished, the epoch_action method will be called. In this method, you can
            update ``lr`` etc. The follow is an example of epoch_action:

            >>> class EpochAction(object):
            >>>     def __init__(self, optim):
            >>>         super(SupervisedTrainer, self).__init__()
            >>>         self.reduce = torch.optim.lr_scheduler.ReduceLROnPlateau(optim, mode="max")
            >>>
            >>>     # The complete method signature is:
            >>>     # def __call__(self, *, model, optimizer, criterion, lr_scheduler,
            >>>     #               train_loss, train_acc, val_loss, val_acc, lr):
            >>>     def __call__(self, *, val_acc, *args, **kwargs):
            >>>         self.reduce.step(val_acc)

        :param checkpoint_interval: the interval of save parameters, the trainer will not save parameters if this param
            if 0.
        :param device: the device used for training.
        :param console_out: redirect print.
        :param result_dir: the directory where the results are saved.
        """
        super(SupervisedTrainer, self).__init__()
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.lr_scheduler = lr_scheduler

        self.init_model_path = init_model_path
        self.init_optim_path = init_optim_path

        self.batch_size = batch_size
        self.train_dataloader, self.val_dataloader = self.__split_dataset(dataset)

        self.epoch = epoch
        self.epoch_action = epoch_action
        self.checkpoint_interval = checkpoint_interval

        self.device = device

        if console_out is None:
            self.console_out = sys.stdout
        else:
            if type(console_out) == str:
                self.console_out = open(console_out, "w")
            else:
                self.console_out = console_out
        self.result_dir = result_dir

        self.start_time = int(time.time())
        self.history = self.History([], [], [], [], [])

    def mount_dataset(self, dataset, val_dataset=None, *, val_ratio=0.3, batch_size=32) -> None:
        """
        mount dataset to this trainer.

        :param dataset: the complete dataset or train dataset.
        :param val_dataset: validate dataset, if it's None, this method will split validate dataset from ``dataset``.
        :param val_ratio: the ratio of validate dataset when split.
        :param batch_size: the batch size.
        :return:
        """
        if dataset is None:
            raise ValueError("dataset cannot be None.")
        if batch_size is not None:
            if type(batch_size) != int:
                raise TypeError("batch_size only accepts int")
            self.batch_size = batch_size
        if val_dataset is None:
            self.train_dataloader, self.val_dataloader = self.__split_dataset(dataset, val_ratio)
        else:
            self.train_dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
            self.val_dataloader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=True)

    def mount_dataloader(self, train_dataloader, val_dataloader) -> None:
        """
        Generally, this method is not recommended.

        Only when the ``mount_dataset`` method unmet demand, you can directly mount a ``train_dataloader`` and a
        ``val_dataloader``.

        :param train_dataloader: dataloader used for training.
        :param val_dataloader: dataloader used for validating.
        :return:
        """
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader

    def __split_dataset(self, dataset, val_ratio=0.3) -> tuple:
        if dataset is None:
            return None, None
        dataset_len = len(dataset)
        val_len = int(val_ratio * dataset_len)
        train_len = dataset_len - val_len
        t, v = random_split(dataset, (train_len, val_len))
        return (DataLoader(t, batch_size=self.batch_size, shuffle=True),
                DataLoader(v, batch_size=self.batch_size, shuffle=True))

    def train(self) -> dict:
        self.__pre_train()
        self.__train()
        self.__post_train()
        return {
            "train_acc": self.history.train_acc[-1],
            "val_acc": self.history.val_acc[-1]
        }

    def test(self, init_model_path, dataset=None, *, dataloader=None) -> tuple:
        """
        calculate the predict accuracy in dataset.

        :param dataset: the dataset for predicting.
        :param dataloader: if dataloader if not None, the ``dataset`` param will be ignored.
        :return: a tuple ``(loss, correct, total)``
        """
        self.console_out.write("[INFO] Test started.")
        if dataloader is None:
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        if init_model_path is None:
            self.console_out.write("[WARN] test model has no pre-trained parameters.")
        else:
            if os.path.exists(init_model_path):
                self.console_out.write("[INFO] load model parameters.\n")
                model_parameters = torch.load(init_model_path, map_location=self.device)
                self.model.load_state_dict(model_parameters)
            else:
                self.console_out.write("[INFO] model parameters not exists.\n")

        self.model = self.model.to(self.device)
        with torch.no_grad():
            loss, correct, total = self._epoch_update(dataloader)
        self.console_out.write("[INFO] Test ended.")
        return loss, correct, total

    def __load_parameters(self):
        if self.init_model_path is not None:
            if os.path.exists(self.init_model_path):
                self.console_out.write("[INFO] load model parameters.\n")
                model_parameters = torch.load(self.init_model_path, map_location=self.device)
                self.model.load_state_dict(model_parameters)
            else:
                self.console_out.write("[INFO] model parameters not exists.\n")
        if self.init_optim_path is not None:
            if os.path.exists(self.init_optim_path):
                self.console_out.write("[INFO] load optim parameters.\n")
                optim_parameters = torch.load(self.init_optim_path, map_location=self.device)
                self.optimizer.load_state_dict(optim_parameters)
            else:
                self.console_out.write("[INFO] optim parameters not exists.\n")

    def __pre_train(self):
        os.makedirs(self.result_dir, exist_ok=True)
        os.makedirs(os.path.join(self.result_dir, "checkpoint"), exist_ok=True)
        self.__load_parameters()
        self.model = self.model.to(self.device)

    def __train(self):
        for e in range(self.epoch):
            t_loss, t_correct, t_total = self._epoch_update(self.train_dataloader)
            t_acc = t_correct / t_total
            with torch.no_grad():
                v_loss, v_correct, v_total = self._epoch_update(self.val_dataloader)
                v_acc = v_correct / v_total
            lr = self.optimizer.param_groups[0]["lr"]
            self.console_out.write("[%s] EPOCH %d of %d\n" %
                                   (self.__time_format(int(time.time()) - self.start_time), e + 1, self.epoch))
            self.console_out.write("\tTrain Loss: %.4f, Acc: %.2f%%\n" % (t_loss, 100 * t_acc))
            self.console_out.write("\tVal   Loss: %.4f, Acc: %.2f%%\n" % (v_loss, 100 * v_acc))
            self.console_out.write("\tLR: %f\n" % lr)
            self.console_out.flush()

            self.history.train_loss.append(t_loss)
            self.history.train_acc.append(t_acc)
            self.history.val_loss.append(v_loss)
            self.history.val_acc.append(v_acc)
            self.history.lr.append(lr)

            if self.epoch_action is not None:
                self.epoch_action(model=self.model, optimizer=self.optimizer, criterion=self.criterion,
                                  lr_scheduler=self.lr_scheduler,
                                  train_loss=t_loss, train_acc=t_acc, val_loss=v_loss, val_acc=v_acc, lr=lr)

            if self.lr_scheduler is not None:
                self.lr_scheduler.step()

            if self.checkpoint_interval > 0 and (e + 1) % self.checkpoint_interval == 0:
                torch.save(self.model.state_dict(), self._checkpoint_parameter_path(e + 1))
                torch.save(self.optimizer.state_dict(),  self._checkpoint_optimizer_path(e + 1))

    def __post_train(self):
        with open(self._history_path(), "w") as f:
            f.write(json.dumps({
                "train_loss": self.history.train_loss,
                "val_loss": self.history.val_loss,
                "train_acc": self.history.train_acc,
                "val_acc": self.history.val_acc,
                "lr": self.history.lr
            }, indent=4))
        torch.save(self.model.state_dict(), self._parameter_path())
        torch.save(self.optimizer.state_dict(), self._optimizer_path())
        self.__draw_png()

    def _checkpoint_parameter_path(self, idx):
        return os.path.join(self.result_dir, "checkpoint", "parameter-%d.checkpoint" % idx)

    def _checkpoint_optimizer_path(self, idx):
        return os.path.join(self.result_dir, "checkpoint", "optimizer-%d.checkpoint" % idx)

    def _parameter_path(self):
        return os.path.join(self.result_dir, "parameter.pth")

    def _optimizer_path(self):
        return os.path.join(self.result_dir, "optimizer.pth")

    def _history_path(self):
        return os.path.join(self.result_dir, "history.json")

    def _graph_path(self):
        return os.path.join(self.result_dir, "history.png")

    def _epoch_update(self, dataloader):
        correct = 0
        total = 0
        loss_total = 0
        iter_num = 0
        loss = None

        for i, data in enumerate(dataloader):
            inputs, labels = data[0], data[1]
            inputs = inputs.to(self.device)
            labels = labels.to(self.device)

            if torch.is_grad_enabled():
                self.optimizer.zero_grad()

            outputs = self.model(inputs)

            if torch.is_grad_enabled():
                loss = self.criterion(outputs, labels)

            if torch.is_grad_enabled():
                loss.backward()
                self.optimizer.step()

                loss_total += loss.item()

            iter_num += 1

            _, pred = torch.max(outputs, 1)
            c = (pred == labels)
            for i, label in enumerate(labels):
                correct += c[i].item()
                total += 1

        return loss_total / iter_num, correct, total

    def __time_format(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def __draw_png(self):
        xdata = range(len(self.history.train_acc))

        fig = plt.figure(figsize=(16, 14))
        spec = gridspec.GridSpec(ncols=2, nrows=2, wspace=0.3, hspace=0.4)

        # Loss
        fig.add_subplot(spec[0, 0])
        plt.title("Loss")
        plt.plot(xdata, self.history.train_loss, label="train")
        plt.plot(xdata, self.history.val_loss, label="val")
        plt.grid()
        plt.legend()

        # Acc
        fig.add_subplot(spec[0, 1])
        plt.title("Accuracy")
        plt.plot(xdata, self.history.train_acc, label="train")
        plt.plot(xdata, self.history.val_acc, label="val")
        plt.grid()
        plt.legend()

        # LR
        fig.add_subplot(spec[1, :])
        plt.title("LR")
        plt.plot(xdata, self.history.lr)
        plt.grid()

        plt.savefig(self._graph_path())
