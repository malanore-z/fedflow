"""
Process communication
=====================

classes in this source file are used for communication among processes, user should not use them directly. the start and
stop action of listener should only be called in fedflow framework.
"""

__all__ = [
    "Handler",
    "Message",
    "MessageListener"
]

import abc
import logging
import threading
import uuid
import multiprocessing
from collections import namedtuple


Message = namedtuple("Message", ["source", "cmd", "data"])
Message.__doc__ = "The message data structure communication among processes."
Message.source.__doc__ = "where message from"
Message.cmd.__doc__ = "the command of this message"
Message.data.__doc__ = "the payload data of this message"


class Handler(object):

    """
    The basic class of message handler
    """

    @abc.abstractmethod
    def handle(self, source: str, cmd: str, data: dict) -> None:
        """
        handle message from other process.

        :param source: where message from, generally, it is a uuid string.
        :param cmd: command, it represents the action to be performed.
        :param data: the payload data of message.
        :return:
        """
        pass


class SystemHandler(Handler):

    """
    The self-message handler used by MessageListener
    """

    def handle(self, source: str, cmd: str, data: dict):
        # Nothing to do
        pass


class DefaultHandler(Handler):

    """
    The default handler, it is only used to avoid null pointer exception.
    """

    def handle(self, source: str, cmd: str, data: dict) -> None:
        # Nothing to do
        logging.getLogger("fedflow.msglistener").warning("No default handler.")


class MessageListener(object):

    logger = logging.getLogger("fedflow.msglistener")

    # uuid source
    __source = uuid.uuid4()
    # the handler for self-message
    __system_handler = SystemHandler()
    # the default handler for message which has no specify handler
    __default_handler = DefaultHandler()
    # handlers for specify source
    __handlers = {}
    # the message queue for all processes
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
                # the message from MessageListener
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
    def register_handler(cls, source: str, handler: Handler, overwrite=False) -> None:
        """
        register handler for specify source.

        :param source: every handler need a source, and the source cannot be same to the source of MessageListener
        :param handler: an instance of subclass of Handler
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
        """
        register default handler and the action will overwrite previous default handler.

        :param default_handler: an instance of subclass of Handler, it will handle all message which has no specify
            handler. In init, the default handler will do nothing.
        :return:
        """
        if default_handler is None:
            cls.logger.warning("default handler cannot be None.")
            return
        cls.logger.info("update default handler.")
        cls.__default_handler = default_handler

    @classmethod
    def stop(cls):
        """
        stop listening.

        :return:
        """
        cls.logger.info("attempt stop.")
        # send stop message to self
        msg = Message(cmd="STOP", source=cls.__source, data={})
        cls.__mq.put(msg)

    @classmethod
    def mq(cls) -> multiprocessing.Queue:
        """
        Get message queue

        :return:
        """
        return cls.__mq
