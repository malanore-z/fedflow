import abc
import random


class NoniidSplit(object):

    def __init__(self, seed=None):
        super(NoniidSplit, self).__init__()
        if seed is not None:
            random.seed(seed)

    @abc.abstractmethod
    def split(self, datasets):
        pass

    def _split_by_classes(self, datasets):
        datasets_by_label = []
        max_label = 0
        for data, label in datasets:
            while max_label <= label:
                datasets_by_label.append([])
                max_label += 1

            datasets_by_label[label].append(data)

        for d in datasets_by_label:
            random.shuffle(d)

        return datasets_by_label
