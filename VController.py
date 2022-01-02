# -*- coding: utf-8 -*-
from typing import Any
from Qtui.VC_ui import Ui_MainWindow
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
from queue import Queue
from logging import StreamHandler, getLogger, DEBUG, NullHandler
import json

import VClogging
from VClogging import WriteStream, MyReceiver
from Camera import VideoThread
import Sender
from Keys import KeyPress, Button, Direction, Hat

CURRENT_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))

class Settings():
    def __init__(self) -> None:
        self.logger = getLogger(__name__)
        self.logger.addHandler(NullHandler())
        self.logger.setLevel(DEBUG)
        self.logger.propagate = True

        self.SettingFileName = "Settings.json"
        self.settings = None

        self.LoadSetting()

    def LoadSetting(self)->None:
        isExistSetting = os.path.exists("Settings.json")
        if not isExistSetting:
            self.logger.debug("No configuration file exists.")
            with open(self.SettingFileName, "w") as f:
                init_setting = {'Camera': {'id': 0, 'fps': 30}, 'COM': 1}
                json.dump(init_setting, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
            self.logger.debug("Generated the configuration file.")

        with open(self.SettingFileName, "r") as j:
            settings = json.load(j)
            self.settings=settings
        self.logger.debug("Loaded the configuration file.") 

    def ApplySettings(self, ui):
        
        ui.spinBox_COM.setValue(int(self.settings["COM"]))
        ui.CameraspinBox.setValue(int(self.settings["Camera"]["id"]))
        ui.fpsTxt.setText(str(self.settings["Camera"]["fps"]))


    def SaveSettings(self, ui):
        self.settings["COM"] = int(ui.spinBox_COM.text())
        self.settings["Camera"]["id"] = int(ui.CameraspinBox.text())
        self.settings["Camera"]["fps"] = int(ui.fpsTxt.text())

        
        with open(self.SettingFileName, "w") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))



class MainUI(QMainWindow):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent)

        
        self.redColor = QColor(255, 0, 0)
        self.key_dict = {16777248: "Shift", 16777249: "Ctrl",
                         16777251: "Alt", 16777222: "Ins",
                         16777223: "Del", 16777232: "Home",
                         16777233: "End", 16777238: "PageUp",
                         16777239: "PageDown", 16777250: "Win"}
        self.arrowkey_dict = {16777234: "ArrowLeft", 16777235: "ArrowUp",
                             16777236: "ArrowRight", 16777237: "ArrowDown"}
        self.holding_keys = set([])

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        qApp.installEventFilter(self)
        # print関数のredirect処理
        self.queue = Queue()
        sys.stdout = WriteStream(self.queue)
        sys.stderr = WriteStream(self.queue)
        self.thread_txt = QThread()
        self.my_receiver = MyReceiver(self.queue)
        self.my_receiver.mysignal.connect(self.append_text)
        self.my_receiver.moveToThread(self.thread_txt)
        self.thread_txt.started.connect(self.my_receiver.run)
        self.thread_txt.start()

        self.logger = getLogger(__name__)
        self.logger.addHandler(StreamHandler(sys.stdout))
        self.logger.setLevel(DEBUG)
        self.logger.propagate = True

        self.ui.RightStick.setStyleSheet("border-radius : 64; \
                                          border : 2px solid black")
        self.ui.LeftStick.setStyleSheet("border-radius : 64; \
                                          border : 2px solid black")
        # Status initialize
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.progress = QProgressBar()
        self.progress.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.progress.setMinimumWidth(200)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(100)
        self.status.addPermanentWidget(self.progress)
        self.showMessage("Ready...")

        # Camera settings here

        self.disply_width, self.display_height = 640, 360
        # self.device_list = pymf.get_MF_devices()
        # for i, device_name in enumerate(self.device_list):
        #    self.logger.debug(f"opencv_index: {i}, device_name: {device_name}")
        grey = QPixmap(self.disply_width, self.display_height)
        grey.fill(QColor('darkGray'))

        # ここでSignal/Slotの定義
        self.ui.ButtonL.clicked.connect(self.PressButtonL)
        self.ui.ButtonZL.clicked.connect(self.PressButtonZL)
        self.ui.HatUP.clicked.connect(self.PressHatUP)
        self.ui.HatDOWN.clicked.connect(self.PressHatDOWN)
        self.ui.HatRIGHT.clicked.connect(self.PressHatRIGHT)
        self.ui.HatLEFT.clicked.connect(self.PressHatLEFT)
        self.ui.ButtonCAPTURE.pressed.connect(self.PressButtonCAPTURE)
        self.ui.ButtonZR.pressed.connect(self.PressButtonZR)
        self.ui.ButtonR.pressed.connect(self.PressButtonR)
        self.ui.ButtonX.pressed.connect(self.PressButtonX)
        self.ui.ButtonY.pressed.connect(self.PressButtonY)
        self.ui.ButtonA.pressed.connect(self.PressButtonA)
        self.ui.ButtonB.pressed.connect(self.PressButtonB)
        self.ui.ButtonHome.pressed.connect(self.PressButtonHOME)
        self.ui.ButtonMinus.pressed.connect(self.PressButtonMINUS)
        self.ui.ButtonPlus.pressed.connect(self.PressButtonPLUS)
        self.ui.ButtonCAPTURE.released.connect(self.ReleaseButtonCAPTURE)
        self.ui.ButtonZR.released.connect(self.ReleaseButtonZR)
        self.ui.ButtonR.released.connect(self.ReleaseButtonR)
        self.ui.ButtonX.released.connect(self.ReleaseButtonX)
        self.ui.ButtonY.released.connect(self.ReleaseButtonY)
        self.ui.ButtonA.released.connect(self.ReleaseButtonA)
        self.ui.ButtonB.released.connect(self.ReleaseButtonB)
        self.ui.ButtonHome.released.connect(self.ReleaseButtonHOME)
        self.ui.ButtonMinus.released.connect(self.ReleaseButtonMINUS)
        self.ui.ButtonPlus.released.connect(self.ReleaseButtonPLUS)
        self.ui.pushButton_CameraConnect.clicked.connect(self.PressCameraReload)
        self.ui.pushButton_CameraCapture.clicked.connect(self.Capture)
        self.ui.pushButton_CameraRecord.clicked.connect(self.Rec)
        self.ui.pushButton_OpenCaptureFolder.clicked.connect(self.OpenCaptureDir)
        self.ui.pushButton_reload.clicked.connect(self.CommandReload)
        self.ui.pushButton_start.clicked.connect(self.CommandStart)
        self.ui.checkBox_GUIC.toggled.connect(self.GUIController)
        self.ui.pushButton_clear.clicked.connect(self.ClearLog)
        self.ui.actionQuit.triggered.connect(self.close)


        # self.ui.CameraList.addItems(self.device_list)
        self.ui.Camera.setPixmap(grey)


        

        
        self.Settings = Settings()
        self.Settings.ApplySettings(self.ui)
        self.Keymapping()

        rx = QRegExp("\\d{1,2}")
        validator = QRegExpValidator(rx, self)
        self.ui.fpsTxt.setValidator(validator)


        # create the video capture thread
        self.camera = VideoThread(self.Settings.settings["Camera"]["fps"],self.Settings.settings["Camera"]["id"])
        # connect its signal to the update_image slot
        self.camera.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.camera.reload_camera(self.Settings.settings["Camera"]["id"])
        self.camera.start()

        self.ser = Sender.Sender(self.ui.showSerial.isChecked())
        self.activateSerial()


        

    def showMessage(self, message: Any) -> None:
        self.status.showMessage(message)

    def SetFps(self):
        if int(self.ui.fpsTxt.text()) > 0:
            self.logger.debug(f"Set FPS to {self.ui.fpsTxt.text()}")
            self.camera.fps = self.ui.fpsTxt.text()
            self.camera.resume()
        else:
            self.logger.debug(f"Stop real-time camera updates.")
            self.camera.pause()

    def SetCOM(self):
        self.logger.debug(f"Load COM {self.ui.spinBox_COM.text()}")
        self.activateSerial()

    def PressButtonL(self):
        try:
            #self.logger.debug(f"{sys._getframe().f_code.co_name}")
            self.ui.ButtonL.setDown(True)
            ret = self.keyPress.input(Button.L)
        
        except Exception as e:
            self.logger.error("Error", e)

    def PressButtonZL(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonZL.setDown(True)
        #ret = self.keyPress.input(Button.ZL)

    def PressHatUP(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def PressHatDOWN(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def PressHatRIGHT(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def PressHatLEFT(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def PressButtonCAPTURE(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonCAPTURE.setDown(True)
        ret = self.keyPress.input(Button.CAPTURE)

    def PressButtonZR(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonZR.setDown(True)
        ret = self.keyPress.input(Button.ZR)

    def PressButtonR(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonR.setDown(True)
        ret = self.keyPress.input(Button.R)

    def PressButtonX(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonX.setDown(True)
        ret = self.keyPress.input(Button.X)

    def PressButtonY(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonY.setDown(True)
        ret = self.keyPress.input(Button.Y)

    def PressButtonA(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonA.setDown(True)
        ret = self.keyPress.input(Button.A)

    def PressButtonB(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonB.setDown(True)
        ret = self.keyPress.input(Button.B)

    def PressButtonHOME(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonHome.setDown(True)
        ret = self.keyPress.input(Button.HOME)

    def PressButtonMINUS(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonMinus.setDown(True)
        ret = self.keyPress.input(Button.MINUS)

    def PressButtonPLUS(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonPlus.setDown(True)
        ret = self.keyPress.input(Button.PLUS)

    def ReleaseButtonL(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonL.setDown(False)
        ret = self.keyPress.inputEnd(Button.L)

    def ReleaseButtonZL(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonZL.setDown(False)
        ret = self.keyPress.inputEnd(Button.ZL)



    def ReleaseHatUP(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def ReleaseHatDOWN(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def ReleaseHatRIGHT(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def ReleaseHatLEFT(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        pass

    def ReleaseButtonCAPTURE(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonCAPTURE.setDown(False)
        ret = self.keyPress.inputEnd(Button.CAPTURE)



    def ReleaseButtonZR(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonZR.setDown(False)
        ret = self.keyPress.inputEnd(Button.ZR)

    def ReleaseButtonR(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonR.setDown(False)
        ret = self.keyPress.inputEnd(Button.R)


    def ReleaseButtonX(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonX.setDown(False)
        ret = self.keyPress.inputEnd(Button.X)


    def ReleaseButtonY(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonY.setDown(False)
        ret = self.keyPress.inputEnd(Button.Y)


    def ReleaseButtonA(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonA.setDown(False)
        ret = self.keyPress.inputEnd(Button.A)


    def ReleaseButtonB(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonB.setDown(False)
        ret = self.keyPress.inputEnd(Button.B)


    def ReleaseButtonHOME(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonHome.setDown(False)
        ret = self.keyPress.inputEnd(Button.HOME)


    def ReleaseButtonMINUS(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonMinus.setDown(False)
        ret = self.keyPress.inputEnd(Button.MINUS)


    def ReleaseButtonPLUS(self):
        #self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.ButtonPlus.setDown(False)
        ret = self.keyPress.inputEnd(Button.PLUS)


    def LeftStick(self):
        self.logger.debug("LeftStick")
        self.logger.debug(self.ui.LeftStick.mousePressEvent)

    def RightStick(self):
        self.logger.debug("RightStick")

    def PressCameraReload(self):
        s = str(self.ui.CameraspinBox.text())
        self.camera.CameraID = int(s)
        self.camera.exit()
        self.camera.reload_camera(s)
        self.camera.start()

    def Capture(self):
        # self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.camera.saveCapture()

    def Rec(self):
        self.logger.debug(f"{sys._getframe().f_code.co_name}")

    def OpenCaptureDir(self):
        self.logger.debug(f"{sys._getframe().f_code.co_name}")

    def CommandReload(self):
        self.logger.debug(f"{sys._getframe().f_code.co_name}")

    def CommandStart(self):
        if self.ui.tabWidget_Commands.currentIndex() == 0:
            self.logger.debug(f"{sys._getframe().f_code.co_name}_python")
        elif self.ui.tabWidget_Commands.currentIndex() == 1:
            self.logger.debug(f"{sys._getframe().f_code.co_name}_Mcu")
        
    def GUIController(self):
        self.logger.debug(f"{sys._getframe().f_code.co_name}")

    def ClearLog(self):
        self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.ui.LogArea.clear()

    def Keymapping(self):
        self.logger.debug(f"{sys._getframe().f_code.co_name}")
        self.keymap = {QKeySequence.fromString(j)[0]:[eval(f"self.Press{i}",{"self": self}), eval(f"self.Release{i}",{"self": self})] for i,j in self.Settings.settings['KeyConfig'].items()}
        # self.keymap = {eval("self.{self.Settings.settings[key]}")}

    def activateSerial(self):
        if self.ser.isOpened():
            self.logger.debug('Port is already opened and being closed.')
            self.ser.closeSerial()
            self.keyPress = None
            self.activateSerial()
        else:
            if self.ser.openSerial(self.ui.spinBox_COM.text()):
                self.logger.debug(f"COM Port {self.ui.spinBox_COM.text()} connected successfully.")
                self.keyPress = KeyPress(self.ser)


    @pyqtSlot(str)
    def append_text(self, text):
        self.ui.LogArea.moveCursor(QTextCursor.End)
        self.ui.LogArea.insertPlainText(text)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.ConvertCV2Qt(cv_img)
        self.ui.Camera.setPixmap(qt_img)

    def ConvertCV2Qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def closeEvent(self, event):
        confirmObject = QMessageBox.question(self, 'Message', 'Are you sure to quit?', QMessageBox.Ok,
                                             QMessageBox.Cancel)
        if confirmObject == QMessageBox.Ok:
            self.camera.kill()
            self.Settings.SaveSettings(self.ui)
            event.accept()
        else:
            event.ignore()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            '''イベントタイプが「キーボードが何か押された時」、下記コードを実行する。'''
            key = event.key()
            mod = event.modifiers()
            if event.isAutoRepeat():
                return True
            try:
                if key in self.key_dict.keys():
                    #self.logger.debug(f"press {self.key_dict[key]}")
                    self.holding_keys |= set([self.key_dict[key]])
                    if key in self.keymap.keys():
                        self.keymap[key][0]()
                elif key in self.arrowkey_dict.keys():
                    #self.logger.debug(f"press {self.arrowkey_dict[key]}")
                    self.holding_keys |= set([self.arrowkey_dict[key]])
                    if key == 16777234:
                        self.keyPress.input(Direction.LEFT)
                    elif key == 16777235:
                        self.keyPress.input(Direction.UP)
                    elif key == 16777236:
                        self.keyPress.input(Direction.RIGHT)
                    elif key == 16777237:
                        self.keyPress.input(Direction.DOWN)
                else:
                    #self.logger.debug(f"press {QKeySequence(key).toString()}")  # 押されたキー名を表示する。
                    self.holding_keys |= set([QKeySequence(key).toString()])
                    if key in self.keymap.keys():
                        self.keymap[key][0]()
                    #self.logger.debug(f"press {key}")  # 押されたキー名を表示する。
                    #self.logger.debug(f"holding {self.holding_keys}")
            except Exception as e:
                self.logger.error(e)
            return True
        return False           

    #def keyPressEvent(self, event):
    #    '''キーが離された場合に呼ばれる。
    #    '''
    #    if event.isAutoRepeat():
    #        return
    #    key = event.key()
    #    try:
    #        if key in self.key_dict.keys():
    #            self.logger.debug(f"press {self.key_dict[key]}")
    #            self.holding_keys |= set([self.key_dict[key]])
    #            if key in self.keymap.keys():
    #                self.keymap[key][0]()
    #        else:
    #            #self.logger.debug(f"press {QKeySequence(key).toString()}")  # 押されたキー名を表示する。
    #            self.holding_keys |= set([QKeySequence(key).toString()])
    #            if key in self.keymap.keys():
    #                self.keymap[key][0]()
    #            #self.logger.debug(f"press {key}")  # 押されたキー名を表示する。
    #            #self.logger.debug(f"holding {self.holding_keys}")
    #    except Exception as e:
    #        self.logger.error(e)

    def keyReleaseEvent(self, event):
        '''キーが離された場合に呼ばれる。
        '''
        if event.isAutoRepeat():
            return
        key = event.key()
        try:
            
            if key in self.key_dict.keys():
                #self.logger.debug(f"release {self.key_dict[key]}")
                self.holding_keys -= set([self.key_dict[key]])
                if key in self.keymap.keys():
                    self.keymap[key][1]()
            elif key in self.arrowkey_dict.keys():
                #self.logger.debug(f"release {self.arrowkey_dict[key]}")
                self.holding_keys -= set([self.arrowkey_dict[key]])
                if key == 16777234:
                    self.keyPress.inputEnd(Direction.LEFT)
                elif key == 16777235:
                    self.keyPress.inputEnd(Direction.UP)
                elif key == 16777236:
                    self.keyPress.inputEnd(Direction.RIGHT)
                elif key == 16777237:
                    self.keyPress.inputEnd(Direction.DOWN)
            elif type(key) is int:
                #self.logger.debug(f"release {QKeySequence(key).toString()}")  # 離されたキー名を表示する。
                self.holding_keys -= set([QKeySequence(key).toString()])
                if key in self.keymap.keys():
                    self.keymap[key][1]()
                #self.logger.debug(f"release {key}")  # 離されたキー名を表示する。
            #self.logger.debug(f"holding {self.holding_keys}")
        except Exception as e:
            self.logger.error("error", e)


if __name__ == '__main__':
    logger = VClogging.root_logger()
    app = QtWidgets.QApplication(sys.argv)
    window = MainUI()
    window.show()
    sys.exit(app.exec_())
