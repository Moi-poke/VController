from PyQt5.Qt import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets
import os.path
import sys
# import pymf as pymf
import cv2
import numpy as np
import time
import datetime
from queue import Queue
from logging import StreamHandler, getLogger, DEBUG, NullHandler


def imwrite(filename: str, img, params=None):
    logger = getLogger(__name__)
    logger.addHandler(NullHandler())
    logger.setLevel(DEBUG)
    logger.propagate = True
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        logger.error(f"Image Write Error: {e}")
        return False


class VideoThread(QThread):
    """
    Loading Camera class
    contains ImageProcessing
    """
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, fps, CameraID):
        super().__init__()
        self.logger = getLogger(__name__)
        self.logger.addHandler(StreamHandler(sys.stdout))

        self.logger.setLevel(DEBUG)
        self.logger.propagate = True

        self.is_paused = False

        self.CameraID = CameraID
        self.capture_size = (1280, 720)
        self.fps = fps
        self.camera = None
        self.temp_cameraID = None
        self.cv_img = None
        self.capture_dir = "Captures"

    def run(self):
        # capture from web cam
        while True:
            if not self.is_paused:
                if self.camera is not None and self.camera.isOpened():
                    ret, self.cv_img = self.camera.read()
                    if ret:
                        self.change_pixmap_signal.emit(self.cv_img)
                    self.busy_wait(1 / np.float64(self.fps))

    def reload_camera(self, CID):
        if self.CameraID == self.temp_cameraID:
            return
        else:
            if self.camera is not None and self.camera.isOpened():
                self.camera.release()
                self.camera = None
                self.logger.debug(f"Camera released. Now reloading...")
            try:
                self.camera = cv2.VideoCapture(self.CameraID, cv2.CAP_DSHOW)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_size[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_size[1])
                self.temp_cameraID = self.CameraID
                self.logger.debug(f"Done loading camera {CID}")
            except Exception as e:
                self.logger.error(e)

    def saveCapture(self, crop: list[int] = None, crop_ax: list[int] = None, filename: str = None):
        crop = None
        if crop_ax is None:
            crop_ax = [0, 0, 1280, 720]

        dt_now = datetime.datetime.now()
        if filename is None or filename == "":
            filename = dt_now.strftime('%Y-%m-%d_%H-%M-%S') + ".png"
        else:
            filename = filename + ".png"

        if crop is None:
            image = self.cv_img
        else:
            image = self.cv_img

        if not os.path.exists(self.capture_dir):
            os.makedirs(self.capture_dir)
            self.logger.debug("Created Capture folder")
        save_path = os.path.join(self.capture_dir, filename)
        try:
            imwrite(save_path, image)
            self.logger.debug(f"Capture succeeded: {save_path}")
        except cv2.error as e:
            self.logger.error(f"Capture Failed :{e}")

    def busy_wait(self, dt):
        current_time = time.perf_counter()
        while time.perf_counter() < current_time + dt:
            pass

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def kill(self):
        self.logger.debug("Kill VideoThread")
        self.terminate()
