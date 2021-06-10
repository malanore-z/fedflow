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

    History = namedtuple("History", ["train_loss", "train_acc", "val_loss", "val_acc", "lr"])

    def __init__(self, model, optimizer, criterion, lr_scheduler=None, *,
                 init_model_path=None,
                 init_optim_path=None,
                 dataset=None,
                 batch_size=32,
                 epoch=50,
                 epoch_action=None,
                 checkpoint_interval=10,
                 device="cuda:0",
                 console_out=None):
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

        self.start_time = int(time.time())
        self.history = self.History([], [], [], [], [])

    def mount_dataset(self, dataset, val_dataset=None, *, val_ratio=0.3, batch_size=32):
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

    def mount_dataloader(self, train_dataloader, val_dataloader):
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader

    def load_model(self, parameter_path=None, optimizer_path=None):
        if parameter_path is None:
            parameter_path = "parameter.pth"
            if optimizer_path is None:
                optimizer_path = "optimizer.pth"
        self.model.load_state_dict(torch.load(parameter_path, map_location=self.device))
        self.model = self.model.to(self.device)
        if optimizer_path is not None:
            self.optimizer.load_state_dict(torch.load(optimizer_path, "optimizer.pth"))

    def __split_dataset(self, dataset, val_ratio=0.3):
        if dataset is None:
            return None, None
        dataset_len = len(dataset)
        val_len = int(val_ratio * dataset_len)
        train_len = dataset_len - val_len
        t, v = random_split(dataset, (train_len, val_len))
        return (DataLoader(t, batch_size=self.batch_size, shuffle=True),
                DataLoader(v, batch_size=self.batch_size, shuffle=True))

    def train(self):
        self.__pre_train()
        self.__train()
        self.__post_train()
        return {
            "train_acc": self.history.train_acc[-1],
            "val_acc": self.history.val_acc[-1]
        }

    def test(self, dataset=None, *, dataloader=None):
        if dataloader is None:
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        with torch.no_grad():
            loss, correct, total = self._epoch_train(dataloader)
        return loss, correct, total

    def __pre_train(self):
        os.makedirs("checkpoint", exist_ok=True)
        if self.init_model_path is not None:
            if os.path.exists(self.init_model_path):
                self.console_out.write("[INFO] load model parameters.")
                model_parameters = torch.load(self.init_model_path, map_location=self.device)
                self.model.load_state_dict(model_parameters)
            else:
                self.console_out.write("[INFO] model parameters not exists.")
        if self.init_optim_path is not None:
            if os.path.exists(self.init_optim_path):
                self.console_out.write("[INFO] load optim parameters.")
                optim_parameters = torch.load(self.init_optim_path, map_location=self.device)
                self.optimizer.load_state_dict(optim_parameters)
            else:
                self.console_out.write("[INFO] optim parameters not exists.")
        self.model = self.model.to(self.device)

    def __train(self):
        for e in range(self.epoch):
            t_loss, t_correct, t_total = self._epoch_train(self.train_dataloader)
            t_acc = t_correct / t_total
            with torch.no_grad():
                v_loss, v_correct, v_total = self._epoch_train(self.val_dataloader)
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
                torch.save(self.model.state_dict(), "checkpoint/parameter-%d.checkpoint" % (e + 1))
                torch.save(self.optimizer.state_dict(), "checkpoint/oprtimizer-%d.checkpoint" % (e + 1))

    def __post_train(self):
        with open("history.json", "w") as f:
            f.write(json.dumps({
                "train_loss": self.history.train_loss,
                "val_loss": self.history.val_loss,
                "train_acc": self.history.train_acc,
                "val_acc": self.history.val_acc,
                "lr": self.history.lr
            }, indent=4))
        torch.save(self.model.state_dict(), "parameter.pth")
        torch.save(self.optimizer.state_dict(), "optimizer.pth")
        self.__draw_png()

    def _epoch_train(self, dataloader):
        correct = 0
        total = 0
        loss_total = 0
        iter_num = 0

        for i, data in enumerate(dataloader):
            inputs, labels = data
            inputs = inputs.to(self.device)
            labels = labels.to(self.device)

            if torch.is_grad_enabled():
                self.optimizer.zero_grad()

            outputs = self.model(inputs)
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

        plt.savefig("history.png")
