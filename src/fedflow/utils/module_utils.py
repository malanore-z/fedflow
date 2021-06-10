import importlib
import inspect
import os
import shutil
import sys
from pathlib import PurePath


class ModuleUtils(object):

    @classmethod
    def migrate_module(cls, src, dst, dst_name=None):
        src_name = os.path.basename(src)
        os.makedirs(dst, exist_ok=True)
        if dst_name is None:
            if src_name.endswith(".py"):
                dst_name = src_name[:-3]
            else:
                dst_name = src_name
        if os.path.isdir(src):
            shutil.copytree(src, PurePath(dst, dst_name).as_posix())
        else:
            shutil.copy(src, PurePath(dst, dst_name + ".py").as_posix())

    @classmethod
    def import_module(cls, name, path=None):
        """
        Import the module dynamically

        :param path: module path
        :param name: module name
        :return: module
        """
        if path is not None:
            sys.path.insert(0, os.path.abspath(path))
        try:
            module = importlib.import_module(name)
        except Exception as e:
            module = None
            print(e)
        if path is not None:
            sys.path.remove(sys.path[0])
        return module

    @classmethod
    def import_config(cls):
        module = cls.import_module("noniid_config")
        if module is None:
            return None
        return getattr(module, "config", None)

    @classmethod
    def import_start(cls):
        module = cls.import_module("noniid_startup")
        if module is None:
            return None
        return getattr(module, "start", None)

    @classmethod
    def exists_module(cls, module):
        try:
            exec("import " + module)
            return True
        except:
            return False

    @classmethod
    def get_name(cls, module, obj):
        if module is None or obj is None:
            raise ValueError("")
        for k, v in module.__dict__.items():
            if v == obj:
                return k
        return None
