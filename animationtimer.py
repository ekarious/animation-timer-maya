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

    WIDTH = 600
    HEIGHT = 370

    def __init__(self, parent=maya_main_window()):
        super(AnimationTimerUI, self).__init__(parent)

        self.setWindowTitle(AnimationTimer.TITLE)
        self.resize(AnimationTimerUI.WIDTH, AnimationTimerUI.HEIGHT)

        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)

        self.create_actions()
        self.create_menu()
        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.timer = ATTimer(self)
        self.file = None
        self.recent_timings = ATRecentTimings(self)

        # Windows attached
        self.preference_window = AnimationTimerPreferences(self)

        # Auto-Populate window
        self.populate()

    # ---

    def create_actions(self):
        """
        Create actions mainly for the main menu.
        """
        # Action : New Timing
        self.action_new_timing = QtGui.QAction(u"New Timing", self)
        self.action_new_timing.setStatusTip(u"Create a new Timing")
        self.action_new_timing.setAutoRepeat(False)
        self.action_new_timing.triggered.connect(self.on_new_file_action_triggered)

        # Action : Open Timing
        self.action_open_timing = QtGui.QAction(u"Open Timing", self)
        self.action_open_timing.setStatusTip(u"Open existing Timing (.timing | .json)")
        self.action_open_timing.setAutoRepeat(False)
        self.action_open_timing.triggered.connect(self.on_open_file_action_triggered)

        # Action : Recent Timing (empty at first)
        self.submenu_recent_timing = QtGui.QMenu(u'Recent Timings', self)

        self.submenu_empty_action = QtGui.QAction(u'Empty', self)
        self.submenu_empty_action.setDisabled(True)

        # Action : Save
        self.action_save_timing = QtGui.QAction(u"Save", self)
        self.action_save_timing.setStatusTip(u"Save Timing")
        self.action_save_timing.setAutoRepeat(False)
        self.action_save_timing.triggered.connect(self.on_save_timing_action_triggered)

        # Action : Save As...
        self.action_save_timing_as = QtGui.QAction(u"Save As ...", self)
        self.action_save_timing_as.setStatusTip(u"Save Timing as ...")
        self.action_save_timing_as.setAutoRepeat(False)
        self.action_save_timing_as.triggered.connect(self.on_save_timing_as_action_triggered)

        # Action : Exit Program
        self.action_exit_app = QtGui.QAction(u"Exit", self)
        self.action_exit_app.setStatusTip(u"Close this script")
        self.action_exit_app.triggered.connect(self.on_exit_app_action_triggered)

        # ---

        # Action : Discard current changes
        self.action_discard_current_changes = QtGui.QAction(u"Discard changes", self)
        self.action_discard_current_changes.setStatusTip(u"Discard all changes made since you opened/created this timing.")
        self.action_discard_current_changes.setAutoRepeat(False)
        # self.action_discard_current_changes.triggered.connect(self.on_discard_changes)

        # Action : Open Preference Window
        self.action_preferences_window = QtGui.QAction(u"Preferences", self)
        self.action_preferences_window.setStatusTip(u"Open the preferences window")
        self.action_preferences_window.triggered.connect(self.open_preference_window)

        # ---

        # Action : Show on Maya TimeLine
        self.action_timing_on_timeline = QtGui.QAction(u"Show on Timeline", self)
        self.action_timing_on_timeline.setStatusTip(u"Show on Maya Timeline")
        self.action_timing_on_timeline.setCheckable(True)
        # self.action_timing_on_timeline.triggered.connect()
        self.action_timing_on_timeline.setDisabled(True)

        # ---

        # Action : Reset Window Size
        self.action_reset_window_size = QtGui.QAction(u"Reset window size", self)
        self.action_reset_window_size.setAutoRepeat(False)
        self.action_reset_window_size.setStatusTip(u"Reset the window to its original size")
        # self.action_reset_window_size.triggered.connect(self.on_action_reset_window_size)

        # Action : Show / Hide Interval Column
        self.action_column_interval = QtGui.QAction(u"Toggle Interval Column", self)
        self.action_column_interval.setStatusTip(u"Toggle the visibility of the Interval column")
        self.action_column_interval.setCheckable(True)
        # self.action_column_interval.triggered.connect(self.on_action_column_triggered)

        # Action : Show / Hide Note Column
        self.action_column_note = QtGui.QAction(u"Toggle Note Column", self)
        self.action_column_note.setStatusTip(u"Toggle the visibility of the Note column")
        self.action_column_note.setCheckable(True)
        # self.action_column_note.triggered.connect(self.on_action_column_triggered)

        # Action : Always on Top
        self.action_always_on_top = QtGui.QAction(u"Always on Top", self)
        self.action_always_on_top.setCheckable(True)
        self.action_always_on_top.setStatusTip(u"Toggle the window to always on top of the screen")
        # self.action_always_on_top.triggered.connect(self.on_window_always_on_top_triggered)

        # ---

        # Action : Documentations
        self.action_open_docs = QtGui.QAction(u"Documentation", self)
        self.action_open_docs.setStatusTip(u"Open the Documentation inside a web browser")
        # self.action_open_docs.triggered.connect(self.on_open_documentation_triggered)

        # Action : Add to Shelf
        self.action_add_to_shelf = QtGui.QAction(u"Add to Shelf", self)
        self.action_add_to_shelf.setStatusTip(u"Add a shortcut to the selected shelf.")
        # self.action_add_shelf.triggered.connect(self.on_add_to_shelf)

        # Action : About Window
        self.action_about_window = QtGui.QAction(u"About", self)
        self.action_about_window.setStatusTip(u"About Animation Timer")
        self.action_about_window.setAutoRepeat(False)
        self.action_about_window.triggered.connect(self.open_about_window)

    def create_menu(self):
        """
        Create the main menu and associates actions to it.
        """
        menubar = self.menuBar()

        # File menu
        self.menubar_file = menubar.addMenu("File")
        self.menubar_file.setTearOffEnabled(True)
        self.menubar_file.addAction(self.action_new_timing)
        self.menubar_file.addAction(self.action_open_timing)
        self.menubar_file.addSeparator()
        self.menubar_file.addMenu(self.submenu_recent_timing)
        self.menubar_file.addSeparator()
        self.menubar_file.addAction(self.action_save_timing)
        self.menubar_file.addAction(self.action_save_timing_as)
        self.menubar_file.addSeparator()
        self.menubar_file.addAction(self.action_exit_app)

        # Edit menu
        self.menubar_edit = menubar.addMenu("Edit")
        self.menubar_edit.setTearOffEnabled(True)
        self.menubar_edit.addAction(self.action_discard_current_changes)
        self.menubar_edit.addSeparator()
        self.menubar_edit.addAction(self.action_preferences_window)

        # Maya menu
        self.menubar_maya = menubar.addMenu("Maya")
        self.menubar_maya.addAction(self.action_timing_on_timeline)

        # Window menu
        self.menubar_window = menubar.addMenu("Window")
        self.menubar_window.addAction(self.action_reset_window_size)
        self.menubar_window.addSeparator()
        self.menubar_window.addAction(self.action_column_interval)
        self.menubar_window.addAction(self.action_column_note)
        self.menubar_window.addSeparator()
        self.menubar_window.addAction(self.action_always_on_top)

        # Help menu
        self.menubar_help = menubar.addMenu("Help")
        self.menubar_help.addAction(self.action_open_docs)
        self.menubar_help.addAction(self.action_add_to_shelf)
        self.menubar_help.addSeparator()
        self.menubar_help.addAction(self.action_about_window)

    def create_controls(self):
        """
        Create controls (aka interface Controllers).
        """
        # Timer
        self.timer_font = QtGui.QFont()
        self.timer_font.setPixelSize(36)

        self.timer_label = QtGui.QLabel(u"00:00:000")
        self.timer_label.setFont(self.timer_font)
        self.timer_label.setFixedHeight(60)
        self.timer_label.setStyleSheet("""
                                       margin-top: -10px;
                                       """)

        self.timer_help = QtGui.QLabel(u"min : sec : millisec")
        self.timer_help.setStyleSheet("""
                                      margin-top:15px;
                                      color:#757575;
                                      font-style:italic;
                                      padding:0;
                                      """)

        # FPS
        self.fps_label = QtGui.QLabel()
        self.fps_label.setNum(24)

        self.fps_help = QtGui.QLabel(u"fps")
        self.fps_help.setStyleSheet("""
                                    margin-top:15px;
                                    color:#757575;
                                    font-style:italic;
                                    padding:0;
                                    """)

        # Frames
        self.frame_counter_label = QtGui.QLabel()
        self.frame_counter_label.setNum(0)

        self.frame_counter_help = QtGui.QLabel(u"frame")
        self.frame_counter_help.setStyleSheet("""
                                              margin-top:15px;
                                              color:#757575;
                                              font-style:italic;
                                              padding:0;
                                              """)

        # Central Area
        self.central_list = ATCenterList(self)

        # File Info
        self.file_info_label = QtGui.QLabel(u"No file currently loaded")
        self.file_info_label.setContentsMargins(10, 0, 10, 0)

        # Buttons
        self.start_btn = QtGui.QPushButton(u"Start")
        self.stop_btn = QtGui.QPushButton(u"Stop")

        self.reset_btn = QtGui.QPushButton()
        self.options_btn = QtGui.QPushButton()
        self.sound_btn = QtGui.QPushButton()

    def create_layout(self):
        """
        Create the layout of the Interface.
        """
        # Timer Bar Layout
        timer_bar_layout = QtGui.QGridLayout()
        timer_bar_layout.setContentsMargins(10, 0, 10, 0)
        timer_bar_layout.setColumnStretch(0, 1)
        timer_bar_layout.setColumnStretch(2, 1)
        timer_bar_layout.addWidget(self.fps_label, 0, 0, 0, 1, QtCore.Qt.AlignLeft)
        timer_bar_layout.addWidget(self.fps_help, 1, 0, 1, 1, QtCore.Qt.AlignLeft)
        timer_bar_layout.addWidget(self.timer_label, 0, 1, 0, 1, QtCore.Qt.AlignCenter)
        timer_bar_layout.addWidget(self.timer_help, 1, 1, 1, 1, QtCore.Qt.AlignCenter)
        timer_bar_layout.addWidget(self.frame_counter_label, 0, 2, 0, 1, QtCore.Qt.AlignRight)
        timer_bar_layout.addWidget(self.frame_counter_help, 1, 2, 1, 1, QtCore.Qt.AlignRight)

        # Set Main Layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(0, 6, 0, 10)
        main_layout.addLayout(timer_bar_layout)
        main_layout.addWidget(self.central_list)
        main_layout.addWidget(self.start_btn)
        main_layout.addWidget(self.file_info_label)

        self.central_widget.setLayout(main_layout)

    def create_connections(self):
        """
        Create connections from controllers to actions inside the
        program.
        """
        pass

    # ---

    def populate(self):
        pass

    def open_about_window(self):
        message = u'<h3>%s</h3>' % AnimationTimer.TITLE
        message += u'<p>Version: {0}<br>'.format(AnimationTimer.VERSION)
        message += u'Author:  %s</p>' % AnimationTimer.AUTHOR
        message += u'<a style="color:white;" \
        href="http://www.yannschmidt.com">http://www.yannschmidt.com</a><br>'
        message += u'<p>Copyright &copy; 2015</p>'

        QtGui.QMessageBox.about(
            self,
            u'About',
            message
        )

    def open_preference_window(self):
        self.preference_window.exec_()

    # ---
    # Slots

    def on_new_file_action_triggered(self):
        pass

    def on_open_file_action_triggered(self):
        pass

    def on_save_timing_action_triggered(self):
        pass

    def on_save_timing_as_action_triggered(self):
        pass

    def on_exit_app_action_triggered(self):
        self.close()


class AnimationTimer(object):

    TITLE = u"Animation Timer"
    AUTHOR = u"Yann Schmidt"
    VERSION = u"1.4"
    USER_SCRIPT_DIR = pm.system.internalVar(userScriptDir=True)
    USER_PREFS_DIR = pm.system.internalVar(userPrefDir=True)

    def __init__(self):
        self.settings = AnimationTimer.load_settings_file()
        self.settings.setFallbacksEnabled(False)

    # ---

    @classmethod
    def load_settings_file(cls):
        return QtCore.QSettings(QtCore.QSettings.IniFormat,
                                QtCore.QSettings.UserScope,
                                u'yannschmidt.com/Animation Timer',
                                u'Animation Timer')



class ATTimer(QtCore.QTimer):
    """
    Timer for the main script.
    Holds 2 timers.
    ---
    QTimer for display purpose.
    QElapsedTimer for calculations.
    """
    def __init__(self, parent):
        super(ATTimer, self).__init__(parent)

        # Connections
        self.timeout.connect(self.on_timer_changed)

    def start(self):
        """
        Start the 2 timers simultaneously.
        """
        pass

    def stop(self):
        """
        Stop the 2 timers simultaneously.
        """
        pass

    # ---

    @property
    def elapsed(self):
        return None

    # ---

    def on_timer_changed(self):
        pass


class ATCenterList(QtGui.QTableWidget):
    """
    Center List object.
    """
    def __init__(self, parent):
        super(ATCenterList, self).__init__(parent)


class ATFile(QtCore.QFile):
    """
    File object to manage timing file.
    """
    def __init__(self, name, parent=None):
        super(ATFile, self).__init__(name, parent)
        self.data = None
        self.data_changed = False


class ATRecentTimings(object):
    """
    Manage recent timing files.
    """
    MAX = 10

    def __init__(self, parent=None):
        self.parent = parent
        self.data = list()

    def create(self):
        pass

    def read(self):
        pass

    def update(self, file):
        pass

    def delete(self, file):
        pass

    def clear(self):
        pass

    # ---

    @property
    def count(self):
        return len(self.data)

    # ---

    def _uniqify(self):
        """
        Make sure all files in the list are unique !
        """
        pass


class AnimationTimerOptions(QtGui.QDialog):
    pass


class AnimationTimerPreferences(QtGui.QDialog):
    pass


def show():
    """
    Simply launch the script.
    :return: void
    """
    global atui

    try:
        atui.close()
    except:
        pass

    atui = AnimationTimerUI()
    atui.show()


if __name__ == "__main__":

    try:
        atui.close()
    except:
        pass

    atui = AnimationTimerUI()
    atui.show()
