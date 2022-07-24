__all__ = [
    "Dag",
    "ExecutableDag"
]

import copy
import queue
from typing import Union, Tuple, List, Set, Dict


KeyType = Union[int, str, bytes]


def CHECK_IF(ret, msg):
    if not ret:
        raise ValueError(msg)


def CHECK_EXIST(elem, container, msg):
    if elem not in container:
        raise ValueError(msg)


def CHECK_NOT_EXIST(elem, container, msg):
    if elem in container:
        raise ValueError(msg)


class DagNode(object):

    def __init__(self, key: KeyType, n_in_ports=-1, n_out_ports=-1):
        super(DagNode, self).__init__()
        if key is None or key == "" or key == b"":
            raise ValueError(f"key cannot be None or empty string(bytes)")
        self.__key = key
        self.__n_in_ports = n_in_ports
        self.__n_out_ports = n_out_ports

    @property
    def key(self) -> KeyType:
        return self.__key

    @property
    def n_in_ports(self) -> int:
        return self.__n_in_ports

    @property
    def n_out_ports(self) -> int:
        return self.__n_out_ports


class Dag(object):

    def __init__(self):
        super(Dag, self).__init__()
        self._nodes_by_key: Dict[str, DagNode] = dict()
        self._edges: Dict[str, Dict[str, Tuple[int, int]]] = dict()
        self._reverse_edges: Dict[str, Dict[str, Tuple[int, int]]] = dict()

    def add_node(self, key: str, n_in_ports: int = -1, n_out_ports: int = -1, *, strict=False):
        """

        :param key:
        :param n_in_ports:
        :param n_out_ports:
        :param strict:
        :return:
        """
        if key in self._nodes_by_key:
            if strict:
                raise ValueError(f"{key} already exists.")
            else:
                return
        self._nodes_by_key[key] = DagNode(key, n_in_ports, n_out_ports)
        if key not in self._edges:
            self._edges[key] = dict()

    def del_node(self, key: str):
        """

        :param key:
        :return:
        """
        for pre_key, post_nodes in self._edges.items():
            for post_key in post_nodes.keys():
                if pre_key == key or key == post_key:
                    raise ValueError(f"There is an edge({pre_key}->{post_key}) associated with this node({key}) in this DAG.")
        if key in self._edges:
            del self._edges[key]

    def add_edge(self, pre_key, post_key, pre_port=-1, post_port=-1, *, strict=False):
        """

        :param pre_key:
        :param post_key:
        :param pre_port:
        :param post_port:
        :param strict:
        :return:
        """
        CHECK_EXIST(pre_key, self._nodes_by_key, f"{pre_key} not exists.")
        CHECK_EXIST(post_key, self._nodes_by_key, f"{post_key} not exists.")
        CHECK_IF(self._check_port(pre_port, self._nodes_by_key[pre_key].n_in_ports), f"illegal pre port({pre_port})")
        CHECK_IF(self._check_port(post_port, self._nodes_by_key[post_key].n_out_ports), f"illegal post port({post_port})")

        if post_key in self._edges[pre_key]:
            if strict:
                raise ValueError(f"Edge({pre_key}->{post_key}) already exists.")
            else:
                return

        CHECK_IF(self.__check_conflict(pre_key, post_key), f"Edge({pre_key}->{post_key}) conflicts with exists edges.")

        self._edges[pre_key][post_key] = (pre_port, post_port)
        self._reverse_edges[post_key][pre_key] = (post_port, pre_port)

    def del_edge(self, pre_key, post_key, pre_port=-1, post_port=-1):
        if pre_key in self._edges:
            post_nodes = self._edges[pre_key]
            if post_key in post_nodes:
                ports = post_nodes[post_key]
                if ports == (pre_port, post_port):
                    del post_nodes[post_key]
                    del self._reverse_edges[post_key][pre_key]

    def begin_nodes(self) -> List[str]:
        """

        :return:
        """
        in_degree = self._in_degree()
        nodes = []
        for key, deg in in_degree.items():
            if deg == 0:
                nodes.append(key)
        return nodes

    def topological(self):
        """

        :return:
        """
        in_degree = self._in_degree()
        q = queue.Queue()
        for key, deg in in_degree.items():
            if deg == 0:
                q.put(key)
        nodes = []
        while not q.empty():
            pre_key = q.get()
            for post_key, _ in self._edges[pre_key]:
                in_degree[post_key] -= 1
                if in_degree[post_key] == 0:
                    nodes.append(post_key)
                    q.put(post_key)
        return nodes

    def executable_dag(self):
        return ExecutableDag(self)

    def __deepcopy__(self, memodict={}):
        dag = Dag()
        dag._nodes_by_key = copy.deepcopy(self._nodes_by_key)
        dag._edges = copy.deepcopy(self._edges)
        dag._reverse_edges = copy.deepcopy(self._reverse_edges)
        return dag

    def __check_conflict(self, pre_key, post_key):
        conflict = False

        def dfs_(key):
            global conflict
            for post_key_ in self._edges[key].keys():
                if conflict:
                    return
                if post_key_ == post_key:
                    conflict = True
                    return

        dfs_(pre_key)
        return not conflict

    def _in_degree(self):
        in_degree = dict()
        for key in self._nodes_by_key.keys():
            in_degree[key] = 0
        for _, post_nodes in self._edges.items():
            for post_key in post_nodes.keys():
                in_degree[post_key] += 1
        return in_degree

    def _check_port(self, port, max_port):
        if port == -1 and max_port == -1:
            return True
        if port == -1 or max_port == -1:
            return False
        if 0 <= port < max_port:
            return True
        return False


class ExecutableDag(object):

    def __init__(self, dag: Dag):
        super(ExecutableDag, self).__init__()
        self._edges = copy.deepcopy(dag._edges)
        self._in_degree = dag._in_degree()
        self._q = queue.Queue()
        self._node_seq = []
        for key, deg in self._in_degree.items():
            if deg == 0:
                self._q.put(key)

    def get(self):
        if self._q.empty():
            return None
        return self._q.get()

    def finished(self):
        return len(self._node_seq) < len(self._in_degree)

    def execute(self, node: str):
        CHECK_EXIST(node, self._edges, f"{node} not exists.")
        for post_key in self._edges[node]:
            self._in_degree[post_key] -= 1
            if self._in_degree[post_key] == 0:
                self._q.put(post_key)
                self._node_seq.append(post_key)
