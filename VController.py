# -*- coding: utf-8 -*-
from Qtui.VC_ui import Ui_MainWindow
from PyQt5.Qt import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets
import os.path
import sys
import pymf as pymf
import cv2
print("Hello World!")


device_list = pymf.get_MF_devices()
for i, device_name in enumerate(device_list):
    print(f"opencv_index: {i}, device_name: {device_name}")


CURRENT_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))


class MainUI(QMainWindow):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

# ここで関数の定義


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec_())
