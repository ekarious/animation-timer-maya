# -*- coding: utf-8 -*-

# Animation Timer
# Author: Yann Schmidt
# Maya 2014+

from PySide import QtCore, QtGui
from shiboken import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import maya.cmds as cmds

# Constants
TITLE = u"Animation Timer"
AUTHOR = u"Yann Schmidt"
VERSION = u"0.1a"
USER_SCRIPT_DIR = cmds.internalVar(usd=True)
USER_PREFS_DIR = cmds.internalVar(upd=True)


# Pointer to maya main window
def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)


# Function to get bool from a string
def _str_to_bool(data):
    if isinstance(data, bool):
        return data

    if data == 'true':
        return True
    else:
        return False


def info_display(message):
    return om.MGlobal.displayInfo(message)


def warning_display(message):
    return om.MGlobal.displayWarning(message)


def error_display(message):
    return om.MGlobal.displayError(message)


class AnimationTimerUI(QtGui.QMainWindow):

    def __init__(self, parent=maya_main_window()):
        super(AnimationTimerUI, self).__init__(parent)

        self.setWindowTitle(TITLE)
        self.resize(650, 400)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowStaysOnTopHint)

        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)

        self.create_menu()
        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.populate()

        # Special Windows
        self.preferences_window = ATPreferencesWindow(self)

    def create_menu(self):
        """
        Create the main menu and associate actions
        """
        # Action : New Timing
        action_new = QtGui.QAction(u"New Timing", self)
        action_new.setStatusTip(u"Create a new Timing")
        action_new.setAutoRepeat(False)
        action_new.setDisabled(True)

        # Action : Open Timing
        action_open = QtGui.QAction(u"Open Timing", self)
        action_open.setStatusTip(u"Open existing Timing")
        action_open.setAutoRepeat(False)
        action_open.setDisabled(True)

        # Action : Save
        action_save = QtGui.QAction(u"Save", self)
        action_save.setStatusTip(u"Save Timing")
        action_save.setAutoRepeat(False)
        action_save.setDisabled(True)

        # Action : Save As ...
        action_save_as = QtGui.QAction(u"Save As ...", self)
        action_save_as.setStatusTip(u"Save Timing as ...")
        action_save_as.setAutoRepeat(False)
        action_save_as.setDisabled(True)

        # Action : Close Timing
        action_close = QtGui.QAction(u"Close Timing", self)
        action_close.setStatusTip(u"Close the selected Timing")
        action_close.setAutoRepeat(False)
        action_close.setDisabled(True)

        # Action : Recent Timing

        # Action : Exit Program
        action_exit = QtGui.QAction(u"Exit", self)
        action_exit.setStatusTip(u"Close this window")
        action_exit.triggered.connect(self.close)

        # -----

        # Action : Undo
        action_undo = QtGui.QAction(u"Undo", self)
        action_undo.setStatusTip(u"Undo the last action made")
        action_undo.setDisabled(True)

        # Action : Redo
        action_redo = QtGui.QAction(u"Redo", self)
        action_redo.setStatusTip(u"Redo the last undo")
        action_redo.setDisabled(True)

        # Action : Copy
        action_copy = QtGui.QAction(u"Copy", self)
        action_copy.setStatusTip("Copy selected timing raw(s)")
        action_copy.setDisabled(True)

        # Action : Cut
        action_cut = QtGui.QAction(u"Cut", self)
        action_cut.setStatusTip("Cut selected timing raw(s)")
        action_cut.setDisabled(True)

        # Action : Paste
        action_paste = QtGui.QAction(u"Paste", self)
        action_paste.setStatusTip("Paste")
        action_paste.setDisabled(True)

        # Action : Select All
        action_select_all = QtGui.QAction(u"Select All", self)
        action_select_all.setStatusTip(u"Select all timing raws")
        action_select_all.setDisabled(True)

        # Action : Delete
        action_delete = QtGui.QAction(u"Delete", self)
        action_delete.setStatusTip(u"Delete selected raw(s)")
        action_delete.setDisabled(True)

        # -----

        # Action : Open Preferences Window
        action_preferences = QtGui.QAction(u"Preferences", self)
        action_preferences.setStatusTip(u"Open the Preferences Window")
        action_preferences.setAutoRepeat(False)
        # action_preferences.triggered.connect(self.open_preferences_window)

        # -----

        # Action : Always on Top
        action_always_on_top = QtGui.QAction(u"Always on Top", self)
        action_always_on_top.setCheckable(True)

        # -----

        # Action : Documentations
        userguideAction = QtGui.QAction(u"Documentation", self)
        userguideAction.setStatusTip(u"Open the Documentation"
                                 " inside a web browser")

        # Action : About Window
        action_about = QtGui.QAction(u"About", self)
        action_about.setStatusTip(u"About Animation Timer")
        action_about.setAutoRepeat(False)
        # action_about.triggered.connect(self.open_about_window)

        # Create the menu
        menubar = self.menuBar()

        # File menu
        menu_file = menubar.addMenu("File")
        menu_file.addAction(action_new)
        menu_file.addAction(action_open)
        menu_file.addAction(action_close)
        menu_file.addSeparator()
        menu_file.addAction(action_save)
        menu_file.addAction(action_save_as)
        menu_file.addSeparator()
        menu_file.addAction(action_exit)

        # Edit menu
        menu_edit = menubar.addMenu("Edit")
        menu_edit.addAction(action_undo)
        menu_edit.addAction(action_redo)
        menu_edit.addSeparator()
        menu_edit.addAction(action_copy)
        menu_edit.addAction(action_cut)
        menu_edit.addAction(action_paste)
        menu_edit.addSeparator()
        menu_edit.addAction(action_select_all)
        menu_edit.addAction(action_delete)
        menu_edit.addSeparator()
        menu_edit.addAction(action_preferences)

        # Timing menu

        # Window menu
        menu_window = menubar.addMenu("Window")
        menu_window.addAction(action_always_on_top)

        # Help menu
        menu_help = menubar.addMenu("Help")
        menu_help.addAction(userguideAction)
        menu_help.addAction(action_about)

    def create_controls(self):
        """
        Create the controls
        """
        # Timer
        self.timer_label = QtGui.QLabel("00:00:00")

        # MDI Area
        self.mdi_area = QtGui.QMdiArea()
        self.mdi_area.setViewMode(QtGui.QMdiArea.TabbedView)

        # Buttons
        self.start_btn = QtGui.QPushButton()
        self.stop_btn = QtGui.QPushButton()
        self.reset_btn = QtGui.QPushButton()

        # Labels
        self.fps = QtGui.QLabel("25 fps")

    def create_layout(self):

        # Vertical right buttons interface
        buttons_layout = QtGui.QVBoxLayout()
        buttons_layout.setAlignment(QtCore.Qt.AlignHCenter)
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.reset_btn)

        # Infos
        infos_layout = QtGui.QHBoxLayout()
        # infos_layout.addWidget(self.frames)
        infos_layout.addWidget(self.fps)

        # Top user interface
        user_ui_layout = QtGui.QHBoxLayout()
        user_ui_layout.setAlignment(QtCore.Qt.AlignCenter)
        user_ui_layout.addWidget(self.timer_label)

        # Set Layout for the bottom part
        main_bottom_layout = QtGui.QHBoxLayout()
        main_bottom_layout.setContentsMargins(0, 0, 0, 0)
        main_bottom_layout.addWidget(self.mdi_area)
        main_bottom_layout.addLayout(buttons_layout)

        # Create 2 QWidget for basic Layout
        main_widget_top = QtGui.QWidget()
        main_widget_top.setFixedHeight(50)
        main_widget_top.setStyleSheet("background-color:#000000;")
        main_widget_top.setLayout(user_ui_layout)

        main_widget_bottom = QtGui.QWidget()
        main_widget_bottom.setLayout(main_bottom_layout)

        # Set the Main Layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_widget_top)
        main_layout.addWidget(main_widget_bottom)

        self.central_widget.setLayout(main_layout)

    def create_connections(self):
        pass

    def populate(self):
        pass

    def open_preferences_window(self):
        self.preferences_window.exec_()

    def open_about_window(self):
        """
        Open the about window
        """
        message = u'<h3>%s</h3>' % TITLE
        message += u'<p>Version: {0}<br>'.format(VERSION)
        message += u'Author:  %s</p>' % AUTHOR
        message += u'<a style="color:white;" \
        href="http://yannschmidt.com">http://yannschmidt.com</a><br>'
        message += u'<p>Copyright &copy; 2015 %s</p>' % AUTHOR

        QtGui.QMessageBox.about(
            self,
            u'About',
            message
        )


class AnimationTimer(object):
    pass


class ATPreferencesWindow(QtGui.QDialog):
    pass


if __name__ == "__main__":

    try:
        ui.close()
    except:
        pass

    ui = AnimationTimerUI()
    ui.show()
