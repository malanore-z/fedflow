import logging.config
import os
from logging import Filter

import zcommons as zc


class ColorFilter(Filter):

    colors = {
        logging.DEBUG: zc.FORE_CYAN,
        logging.INFO: zc.FORE_GREEN,
        logging.WARN: zc.FORE_YELLOW,
        logging.WARNING: zc.FORE_YELLOW,
        logging.ERROR: zc.FORE_RED,
        logging.CRITICAL: zc.FORE_MAGENTA
    }

    def __init__(self):
        super(ColorFilter, self).__init__()

    def filter(self, record) -> bool:
        color = self.colors.get(record.levelno, None)
        if color:
            record.levelname = f"{color}{record.levelname}{' ' * (8 - len(record.levelname))}{zc.FORE_RESET}"
        return True


def logging_config(log_level="INFO", log_root="logs", color=True):
    if isinstance(log_level, int):
        log_level = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.WARN: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL"
        }[log_level]
    log_root = os.path.abspath(log_root)
    return {
        "version": 1,
        "formatters": {
            "common": {
                "format": "%(asctime)s %(name)20s [%(levelname)-8s] %(message)s"
            },
            "scheduler": {
                "format": "%(asctime)s [%(levelname)-8s] %(message)s"
            }
        },
        "filters": {
            "color": {
                "()": ColorFilter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "common",
                "stream": "ext://sys.stdout",
                "filters": ["color"] if color else []
            },
            "fedflow": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "common",
                "filename": os.path.join(log_root, "fedflow.log")
            },
            "scheduler": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "scheduler",
                "filename": os.path.join(log_root, "scheduler.log")
            },
            "graph": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "scheduler",
                "filename": os.path.join(log_root, "graph.log")
            }
        },
        "loggers": {
            "fedflow": {
                "level": log_level,
                "handlers": ["console", "fedflow"],
                "propagate": "no"
            },
            "fedflow.scheduler": {
                "level": log_level,
                "handlers": ["console", "scheduler"],
                "propagate": "no"
            },
            "fedflow.graph": {
                "level": log_level,
                "handlers": ["console", "graph"],
                "propagate": "no"
            }
        }
    }


def update_logging_config(log_level="INFO", log_root="logs", color=True):
    config = logging_config(log_level, log_root, color)
    logging.config.dictConfig(config)


def set_level(log_level):
    update_logging_config(log_level=log_level)


def set_root(log_root):
    update_logging_config(log_root=log_root)


def set_color(use_color):
    update_logging_config(color=use_color)


update_logging_config()
