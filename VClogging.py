# -*- coding:utf-8 -*-
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG
import logging
import datetime as dt
from PyQt5.Qt import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from queue import Queue

now = dt.datetime.now()
time = now.strftime('%Y%m%d-%H%M%S')

mapping = {
    "TRACE": " trace ]",
    "DEBUG": " \x1b[0;36mdebug\x1b[0m ",
    "INFO": "  \x1b[0;32minfo\x1b[0m ",
    "WARNING": "  \x1b[0;33mwarn\x1b[0m ",
    "WARN": "  \x1b0;33mwarn\x1b[0m ",
    "ERROR": "\x1b[0;31m error \x1b[0m",
    "ALERT": "\x1b[0;37;41m alert \x1b[0m",
    "CRITICAL": "\x1b[0;37;41m alert \x1b[0m",
}


class WriteStream(object):
    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass


class MyReceiver(QObject):
    mysignal = pyqtSignal(str)

    def __init__(self, queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = queue

    @pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)

class ColorfulHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        record.levelname = mapping[record.levelname]
        super().emit(record)


def root_logger():
    # logging.basicConfig(handlers=[ColorfulHandler()], level=logging.DEBUG)
    # root logger���擾

    logger = getLogger()

    # formatter���쐬
    formatter = Formatter('%(asctime)s %(name)s %(funcName)s [%(levelname)s]: %(message)s')

    # handler���쐬���t�H�[�}�b�^�[��ݒ�
    # handler = ColorfulHandler()
    handler = StreamHandler()
    handler.setFormatter(formatter)

    # �t�@�C���n���h�����쐬
    rh = logging.FileHandler(
        r'./log/log_' + time + '.log',
        encoding='utf-8',
    )

    rh.setFormatter(formatter)

    # logger��handler��ݒ�A�C�x���g�ߑ��̂��߂̃��x����ݒ�
    logger.addHandler(handler)
    logger.addHandler(rh)
    # log level��ݒ�
    logger.setLevel(DEBUG)
    # logger.debug("hello")
    # logger.info("hello")
    # logger.warning("hello")
    # logger.error("hello")
    # logger.critical("hello")

    return logger
