import numpy as np

from fedflow.utils.data.split import NoniidSplit


class DirichletSplit(NoniidSplit):

    def __init__(self, alpha, nsamples, **kwargs):
        super(DirichletSplit, self).__init__(**kwargs)
        self.alpha = alpha
        self.nsamples = nsamples
        self.record = []

    def split(self, datasets):
        datasets_by_label = self._split_by_classes(datasets)

        ret = [[] for _ in range(self.nsamples)]
        for i, d in enumerate(datasets_by_label):
            distribution = np.random.dirichlet([self.alpha for _ in range(self.nsamples)]).tolist()
            self.record.append(distribution)
            data_num = len(d)
            lower, upper, sum_r = 0, 0, 0
            for j in range(self.nsamples):
                sum_r += distribution[j]
                upper = int(data_num * sum_r)
                for data in d[lower:upper]:
                    ret[j].append((data, i))
                lower = upper

        return ret
