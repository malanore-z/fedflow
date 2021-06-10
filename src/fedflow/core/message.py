import abc
import logging
import threading
import uuid
import multiprocessing
from collections import namedtuple


Message = namedtuple("Message", ["source", "cmd", "data"])


class Handler(object):

    @abc.abstractmethod
    def handle(self, source, cmd, data) -> None:
        pass


class SystemHandler(Handler):

    def handle(self, source, cmd, data):
        # Nothing to do
        pass


class DefaultHandler(Handler):

    def handle(self, source, cmd, data) -> None:
        # Nothing to do
        pass


class MessageListener():

    logger = logging.getLogger("fedflow.msglistener")

    __source = uuid.uuid4()
    __system_handler = SystemHandler()
    __default_handler = DefaultHandler()
    __handlers = {}
    __mq = multiprocessing.Queue()

    @classmethod
    def start(cls) -> None:
        t = threading.Thread(target=cls.run)
        t.start()

    @classmethod
    def run(cls) -> None:
        while True:
            msg: Message = cls.__mq.get()
            cls.logger.debug("receive message{source: %s, cmd: %s}", msg.source, msg.cmd)
            if msg.source == cls.__source:
                if msg.cmd == "STOP":
                    cls.logger.info("receive STOP signal.")
                    break
                else:
                    cls.__system_handler.handle(msg.source, msg.cmd, msg.data)
                continue

            handler = cls.__handlers.get(msg.source)
            if handler is not None:
                try:
                    handler.handle(msg.source, msg.cmd, msg.data)
                except Exception as e:
                    cls.logger.error("catch %s.", str(type(e)), exc_info=True, stack_info=True)
            else:
                if cls.__default_handler is not None:
                    cls.__default_handler.handle(msg.source, msg.cmd, msg.data)
                else:
                    cls.logger.warning("no default handler.")

    @classmethod
    def register_handler(cls, source, handler, overwrite=False):
        if source == cls.__source:
            cls.logger.error("cannot register system handler which source is %s", source)
            return
        if overwrite or source not in cls.__handlers:
            cls.logger.info("register handler for %s", source)
            cls.__handlers[source] = handler
        else:
            cls.logger.warning("handler for %s exists.", source)

    @classmethod
    def register_default_handler(cls, default_handler):
        cls.logger.info("update default handler.")
        cls.__default_handler = default_handler

    @classmethod
    def stop(cls):
        cls.logger.info("attempt stop.")
        msg = Message(cmd="STOP", source=cls.__source, data={})
        cls.__mq.put(msg)

    @classmethod
    def mq(cls):
        return cls.__mq
