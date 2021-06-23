
import random

from fedflow.utils.data.split import NoniidSplit


class LabelSplit(NoniidSplit):

    def __init__(self, ratios, duplicate=False, **kwargs):
        """

        :param ratios: Two-dimensional array, label-sample
        """
        super(LabelSplit, self).__init__(**kwargs)
        self.nlabels, self.nsamples = self.__verify_ratios(ratios, duplicate)
        self.ratios = ratios
        self.duplicate = duplicate

    def split(self, datasets):
        datasets_by_label = self._split_by_classes(datasets)

        ret = [[] for _ in range(self.nsamples)]
        if not self.duplicate:
            for i in range(self.nlabels):
                lower, upper = 0, 0
                data_num = len(datasets_by_label[i])
                sum_r = 0
                for j in range(self.nsamples):
                    sum_r += self.ratios[i][j]
                    upper = int(data_num * sum_r)
                    for data in datasets_by_label[i][lower:upper]:
                        ret[j].append((data, i))
                    lower = upper
        else:
            for i in range(self.nlabels):
                data_num = len(datasets_by_label[i])
                for j in range(self.nsamples):
                    random.shuffle(datasets_by_label[i])
                    for data in datasets_by_label[i][:int(data_num * self.ratios[i][j])]:
                        ret[j].append((data, i))

        return ret

    def __verify_ratios(self, ratios, duplicate):
        nlabels = len(ratios)
        nsamples = -1
        for raw in ratios:
            sum_ratio = 0
            for cell in raw:
                sum_ratio += cell
            if not duplicate and round(10000 * sum_ratio) != 10000:
                raise ValueError("sum ratio: %f" % sum_ratio)
            if nsamples == -1 or nsamples == len(raw):
                nsamples = len(raw)
            else:
                raise ValueError("raw: %d, nsamples: %d" % (len(raw), nsamples))
        return nlabels, nsamples
