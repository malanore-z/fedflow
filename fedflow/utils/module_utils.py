"""
Module utils
==============

Module utils for import or migrate module
"""

__all__ = [
    "ModuleUtils"
]

import importlib
import os
import shutil
import sys
from pathlib import PurePath
from typing import Union


class ModuleUtils(object):

    @classmethod
    def migrate_module(cls, src: str, dst: str, dst_name: str = None) -> None:
        """
        migrate a module from ``src`` to ``dst``, and rename it to ``dst_name``.

        :param src: the module source dir.
        :param dst: target dir.
        :param dst_name: new module name, the module name will keep if this param is None.
        :return:
        """
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
    def import_module(cls, name: str, path: str = None):
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
    def exists_module(cls, module: str) -> bool:
        """
        check if module is exists.

        :param module: the module to be checked.
        :return: a bool value.
        """
        try:
            exec("import " + module)
            return True
        except:
            return False

    @classmethod
    def get_name(cls, module, obj) -> Union[str, None]:
        """
        Get the name of ``obj`` in ``module``.

        :param module: the module to found ``obj``.
        :param obj: the obj need to get name.
        :return: a string value represent the name of ``obj`` or None if not found.
        """
        if module is None or obj is None:
            raise ValueError("")
        for k, v in module.__dict__.items():
            if v == obj:
                return k
        return None
