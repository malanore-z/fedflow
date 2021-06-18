"""
Config APIs
===========

All the others codes should use ``Config`` to get fedflow config properties.
"""

__all__ = [
    "Config"
]


import os
import shutil

import yaml


class Config(object):

    # Parameters that can be modified at run time
    __props = {}
    # Parameters that are read from a configuration file and cannot be changed at run time
    __readonly_props = {}

    @classmethod
    def load(cls, path: str =None) -> None:
        """
        load config properties from disk file.

        :param path: config file path, if it's None, will load default config file.
        :return:
        """
        if path is None:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "config.yaml")
            with open(path) as f:
                cls.__readonly_props = yaml.load(f, Loader=yaml.SafeLoader)
        else:
            with open(path) as f:
                cls.__props = yaml.load(f, Loader=yaml.SafeLoader)
        workdir: str = cls.get_property("workdir")
        if workdir is not None:
            workdir = os.path.abspath(workdir)
            cls.set_property("workdir", workdir)

    @classmethod
    def generate_config(cls, path: str =None) -> None:
        """
        generate config file in ``path``.

        :param path: the config file path, if it's None, will be replaced by './config.yaml'.
        :return:
        """
        if path is None:
            path = "config.yaml"
        src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "config.yaml")
        shutil.copy(src_path, path)

    @classmethod
    def set_config(cls, d: dict) -> None:
        """
        Batch update config properties. Generally, this method is not recommend.

        :param d: a dict represent config properties.
        :return:
        """
        cls.__props = d.copy()

    @classmethod
    def get_property(cls, key, default=None):
        """
        Get the value of readonly parameters.

        :param key: a string of the key to get the value
        :param default: return value if key not found
        """
        op_res, val = cls.__get_from_dict(cls.__props,
                                          cls.__split_key(key),
                                          default)
        if op_res:
            return val
        return cls.__get_from_dict(cls.__readonly_props,
                                   cls.__split_key(key),
                                   default)[1]

    @classmethod
    def set_property(cls, key, value):
        """
        Set parameters at run time.

        :param key:
        :param value:
        :return:
        """
        cls.__set_to_dict(cls.__props, cls.__split_key(key), value)

    @classmethod
    def __split_key(cls, key: str):
        if key is None or key.strip() == "":
            raise ValueError("key cannot be none or empty.")
        return key.split(".")

    @classmethod
    def __exists_in_dict(cls, d: dict, k_seq: list):
        if k_seq is None or len(k_seq) == 0:
            return False
        for k in k_seq:
            if k in d:
                d = d[k]
            else:
                return False
        return True

    @classmethod
    def __get_from_dict(cls, d: dict, k_seq: list, default=None):
        if k_seq is None or len(k_seq) == 0:
            raise ValueError("key cannot be none or empty")
        for k in k_seq:
            if k in d:
                d = d[k]
            else:
                return False, default
        return True, d

    @classmethod
    def __set_to_dict(cls, d: dict, k_seq: list, value):
        if k_seq is None or len(k_seq) == 0:
            raise ValueError("key cannot be none or empty")
        for k in k_seq[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[k_seq[-1]] = value


Config.load()
