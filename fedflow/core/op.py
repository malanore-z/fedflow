__all__ = [
    "FedOp"
]

import abc
import logging
from typing import Sequence

from fedflow.core.data import FedData
from fedflow.core.scope import scope as ff_scope

logger = logging.getLogger("fedflow.op")


class FedOp(object):

    def __init__(self, name, graph=None, scope=None, pre_ops=None):
        super(FedOp, self).__init__()
        scope = scope or ff_scope
        self.__name = f"{scope.scope_name}/{name}" if scope.scope_name != "" else name
        self.__graph = graph or self.__default_graph()
        self.__graph.add_op(self, pre_ops)

    @property
    def n_in_ports(self):
        raise NotImplementedError("")

    @property
    def n_out_ports(self):
        raise NotImplementedError("")

    @property
    def name(self):
        return self.__name

    @property
    def graph(self):
        return self.__graph

    @abc.abstractmethod
    def execute(self, inputs: Sequence[FedData]) -> Sequence[FedData]:
        raise NotImplementedError("")

    def __call__(self, inputs: Sequence[FedData]) -> Sequence[FedData]:
        return self.execute(inputs)

    def __default_graph(self):
        from fedflow.core.graph import FedGraph
        return FedGraph.global_instance()
