import copy


class Scope(object):

    def __init__(self):
        super(Scope, self).__init__()
        self.__scopes = []
        self.__tmp_scope_name = None

    @property
    def scope_sequence(self):
        return copy.deepcopy(self.__scopes)

    @property
    def scope_name(self):
        return "/".join(self.__scopes)

    def __call__(self, scope_name):
        self.__tmp_scope_name = scope_name
        return self

    def __enter__(self):
        if self.__tmp_scope_name is None:
            raise ValueError(f"__call__ must be called before __enter__")
        self.__scopes.append(self.__tmp_scope_name)
        self.__tmp_scope_name = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__scopes.remove(self.__scopes[-1])

    def __repr__(self):
        return "/".join(self.__scopes)

    def __str__(self):
        return self.__repr__()


scope = Scope()
