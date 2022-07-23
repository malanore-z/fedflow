import logging
from typing import Sequence

from fedflow.core.data import FedData
from fedflow.core.op import FedOp


logger = logging.getLogger("fedflow.graph")


class FedGraph(object):

    def __init__(self):
        super(FedGraph, self).__init__()
        self.__data_name_set = set()
        self.__op_name_set = set()
        self.__ops = {}

    def add_op(self, op: FedOp, pre_ops: Sequence[FedOp]):
        if op.name in self.__ops:
            raise ValueError(f"duplicate op name({op.name})")
        if pre_ops is None:
            pre_ops = []
        for p_op in pre_ops:
            if p_op not in self.__ops:
                raise ValueError(f"pre op({p_op.name}) cannot found in graph")

        pass

    def __check_conflict(self):
        pass

    def as_global(self):
        global _global_instance
        _global_instance = self

    @classmethod
    def global_instance(cls):
        global _global_instance
        return _global_instance


_global_instance = FedGraph()
