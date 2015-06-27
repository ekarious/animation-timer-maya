# -*- coding: utf-8 -*-

# Aniation Timer
# Author: Yann Schmidt
# Maya 2014+

from PySide import QtCore, QtGui
from shiboken import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import pymel.core as pm

from ast import literal_eval


# Maya MainWindow Reference
def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)


class AnimationTimerUI(QtGui.QMainWindow):
    """
    Main Interface of Animation Timer.
    """
    def __init__(self, parent=maya_main_window()):
        super(AnimationTimerUI, self).__init__(parent)

        self.setWindowTitle(AnimationTimer.TITLE)
        self.resize(600, 370)


class AnimationTimer(object):

    TITLE = u"Animation Timer"
    AUTHOR = u"Yann Schmidt"
    VERSION = u"1.4"
    USER_SCRIPT_DIR = pm.system.internalVar(userScriptDir=True)
    USER_PREFS_DIR = pm.system.internalVar(userPrefDir=True)

    def __init__(self):
        pass


class ATTimer(QtCore.QTimer):
    pass


class ATCenterList(QtGui.QTableWidget):
    pass


class AnimationTimerPreferences(QtGui.QDialog):
    pass


def show():
    pass


if __name__ == "__main__":
    pass
