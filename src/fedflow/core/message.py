import abc
import logging
import threading
import uuid
import multiprocessing
from collections import namedtuple


"""
The message data structure communication among processes.
source: where message from
cmd: the command of this message
data: the payload data of this message
"""
Message = namedtuple("Message", ["source", "cmd", "data"])


class Handler(object):

    """
    The super class of message handler
    """

    @abc.abstractmethod
    def handle(self, source, cmd, data) -> None:
        """
        handle message
        :param source: where message from
        :param cmd: command
        :param data: payload data
        :return:
        """
        pass


class SystemHandler(Handler):

    """
    The handler used by MessageListener
    """

    def handle(self, source, cmd, data):
        # Nothing to do
        pass


class DefaultHandler(Handler):

    """
    The default handler, it is only used to avoid null pointer exception.
    """

    def handle(self, source, cmd, data) -> None:
        # Nothing to do
        logging.getLogger("fedflow.msglistener").warning("No default handler.")


class MessageListener():

    logger = logging.getLogger("fedflow.msglistener")

    # uuid source
    __source = uuid.uuid4()
    __system_handler = SystemHandler()
    __default_handler = DefaultHandler()
    # handlers for specify source
    __handlers = {}
    __mq = multiprocessing.Queue()

    @classmethod
    def start(cls) -> None:
        """
        start listen message
        :return:
        """
        t = threading.Thread(target=cls.run)
        t.start()

    @classmethod
    def run(cls) -> None:
        while True:
            msg: Message = cls.__mq.get()
            cls.logger.debug("receive message{source: %s, cmd: %s}", msg.source, msg.cmd)
            if msg.source == cls.__source:
                if msg.cmd == "STOP":
                    # stop listen
                    cls.logger.info("receive STOP signal.")
                    break
                else:
                    # handle message from MessageListener(main process)
                    cls.__system_handler.handle(msg.source, msg.cmd, msg.data)
                continue

            handler = cls.__handlers.get(msg.source)
            if handler is None:
                handler = cls.__default_handler
            try:
                handler.handle(msg.source, msg.cmd, msg.data)
            except Exception as e:
                cls.logger.error("An error occurred while handling message.", exc_info=True, stack_info=True)

    @classmethod
    def register_handler(cls, source, handler, overwrite=False):
        """
        register proprietary handler for specify source
        :param source:
        :param handler:
        :param overwrite: whether overwrite handler if it exists
        :return:
        """
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
        if default_handler is None:
            cls.logger.warning("default handler cannot be None.")
            return
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
