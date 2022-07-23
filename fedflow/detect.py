__all__ = []


import os
import logging.config

import yaml

from fedflow.config import Config


def detect_config():
    if os.path.exists("config.yaml"):
        Config.load("config.yaml")


detect_config()


def set_debug(d: dict):
    for k in list(d.keys()):
        if k == "level" and type(d[k]) == str:
            d[k] = "DEBUG"
        if type(d[k]) == dict:
            set_debug(d[k])


def detect_logging():
    os.makedirs("logs", exist_ok=True)
    conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "logging.yaml")
    with open(conf_path, "r") as f:
        d = yaml.load(f, yaml.SafeLoader)
    if Config.get_property("debug"):
        set_debug(d)
        d["root"]["level"] = "INFO"
    logging.config.dictConfig(d)


detect_logging()