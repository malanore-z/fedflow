import logging
from typing import Sequence

from fedflow.core.dag import Dag
from fedflow.core.data import FedData
from fedflow.core.op import FedOp


logger = logging.getLogger("fedflow.graph")


class FedGraph(object):

    def __init__(self):
        super(FedGraph, self).__init__()
        self.__data_name_set = set()
        self.__op_name_set = set()
        self.__ops = {}
        self.__dag = Dag()
        self.__op_by_name = dict()
        self.__data_by_name = dict()

    def add_op(self, op: FedOp, pre_ops: Sequence[FedOp] = None):
        if op.name in self.__op_by_name:
            raise ValueError(f"duplicate op name({op.name})")
        if pre_ops is None:
            pre_ops = []
        for i, p_op in enumerate(pre_ops):
            if isinstance(p_op, FedOp):
                pre_ops[i] = (p_op, 0)
        try:
            self.__op_by_name[op.name] = op
            self.__dag.add_node(op.name, op.n_in_ports, op.n_out_ports)
            for i, p_op in enumerate(pre_ops):
                self.__dag.add_edge(p_op[0], op, p_op[1], i)
        except Exception as e:
            if op.name in self.__op_by_name:
                del self.__op_by_name[op.name]
            for p_op in pre_ops:
                self.__dag.del_edge(p_op, op)
            self.__dag.del_node(op.name)
            raise e

    def save(self):
        pass

    def load(self, path):
        pass

    def as_global(self):
        global _global_instance
        _global_instance = self

    @classmethod
    def global_instance(cls):
        global _global_instance
        return _global_instance


_global_instance = FedGraph()
