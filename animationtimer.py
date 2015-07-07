# -*- coding: utf-8 -*-

# Aniation Timer
# Author: Yann Schmidt
# Maya 2014+

from PySide import QtCore, QtGui
from shiboken import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import pymel.core as pm

import os
import shutil
import json
from math import ceil


# Maya MainWindow Reference
def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

def bool_str(data):
    if isinstance(data, bool):
        return data

    return True if data == 'true' else False


class AnimationTimerUI(QtGui.QMainWindow):
    """
    Main Interface of Animation Timer.
    """

    WIDTH = 600
    HEIGHT = 370
    MINIMUM_WIDTH = 400
    MINIMUM_HEIGHT = 300
    MAXIMUM_WIDTH = 800

    def __init__(self, parent=maya_main_window()):
        super(AnimationTimerUI, self).__init__(parent)

        self.setWindowTitle(AnimationTimer.TITLE)
        self.setMinimumSize(AnimationTimerUI.MINIMUM_WIDTH, AnimationTimerUI.MINIMUM_HEIGHT)
        self.setMaximumWidth(AnimationTimerUI.MAXIMUM_WIDTH)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)

        self.create_actions()
        self.create_menu()
        self.create_controls()
        self.create_layout()
        self.create_connections()

        self._read_window_settings()

        self.timer = ATTimer(self)
        self.file = None
        self.recent_timings = ATRecentTimings(self)

        # Windows attached
        self.preference_window = AnimationTimerPreferences(self)
        self.options_window = AnimationTimerOptions(self)

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
        self.action_discard_current_changes.triggered.connect(self.on_discard_changes_triggered)

        # Action : Open Preference Window
        self.action_preferences_window = QtGui.QAction(u"Preferences", self)
        self.action_preferences_window.setStatusTip(u"Open the preferences window")
        self.action_preferences_window.triggered.connect(self.open_preference_window)

        # ---

        # Action : Show on Maya TimeLine
        self.action_timing_on_timeline = QtGui.QAction(u"Show on Timeline", self)
        self.action_timing_on_timeline.setStatusTip(u"Show on Maya Timeline")
        self.action_timing_on_timeline.setCheckable(True)
        self.action_timing_on_timeline.triggered.connect(self.on_show_on_timeline_triggered)
        self.action_timing_on_timeline.setDisabled(True)

        # ---

        # Action : Reset Window Size
        self.action_reset_window_size = QtGui.QAction(u"Reset window size", self)
        self.action_reset_window_size.setAutoRepeat(False)
        self.action_reset_window_size.setStatusTip(u"Reset the window to its original size")
        self.action_reset_window_size.triggered.connect(self.on_action_reset_window_size_triggered)

        # Action : Show / Hide Interval Column
        self.action_column_interval = QtGui.QAction(u"Show Interval Column", self)
        self.action_column_interval.setStatusTip(u"Toggle the visibility of the Interval column")
        self.action_column_interval.setCheckable(True)
        # self.action_column_interval.triggered.connect(self.on_action_column_triggered)

        # Action : Show / Hide Note Column
        self.action_column_note = QtGui.QAction(u"Show Note Column", self)
        self.action_column_note.setStatusTip(u"Toggle the visibility of the Note column")
        self.action_column_note.setCheckable(True)
        # self.action_column_note.triggered.connect(self.on_action_column_triggered)

        # Action : Always on Top
        self.action_always_on_top = QtGui.QAction(u"Always on Top", self)
        self.action_always_on_top.setCheckable(True)
        self.action_always_on_top.setStatusTip(u"Toggle the window to always on top of the screen")
        self.action_always_on_top.triggered.connect(self.on_window_always_on_top_triggered)

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
        self.file_info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.file_info_label.setStyleSheet("""
                                           border-top:1px solid #333333;
                                           margin:0 10px;
                                           padding:8px 0 0 0;
                                           color:#888888;
                                           """)

        # Buttons
        self.start_btn = QtGui.QPushButton(u"Start")
        self.start_btn.setFlat(True)
        self.start_btn.clicked.connect(self.on_start_btn_clicked)
        self.start_btn.setStyleSheet("""
                                     font-size:20px;
                                     """)

        self.vline = QtGui.QFrame()
        self.vline.setFrameShape(QtGui.QFrame.VLine)

        self.stop_btn = QtGui.QPushButton(u"Stop")
        self.stop_btn.clicked.connect(self.on_stop_btn_clicked)
        self.stop_btn.setStyleSheet("""
                                    font-size:20px;
                                    """)
        self.stop_btn.setFlat(True)

        self.reset_btn = QtGui.QPushButton()
        self.reset_btn.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'reset.png')).path()).pixmap(16, 16))
        self.reset_btn.setIconSize(QtCore.QSize(32, 32))
        self.reset_btn.setFixedSize(32, 32)
        self.reset_btn.setToolTip(u"Reset")
        self.reset_btn.clicked.connect(self.on_reset_btn_clicked)
        self.reset_btn.setFlat(True)

        self.options_btn = QtGui.QPushButton()
        self.options_btn.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'options.png')).path()).pixmap(16, 16))
        self.options_btn.setIconSize(QtCore.QSize(32, 32))
        self.options_btn.setFixedSize(32, 32)
        self.options_btn.setToolTip(u"Options Panel")
        self.options_btn.clicked.connect(self.on_options_btn_clicked)
        self.options_btn.setFlat(True)

        self.sound_btn = QtGui.QPushButton()
        self.sound_btn.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'sound.png')).path()).pixmap(16, 16))
        self.sound_btn.setIconSize(QtCore.QSize(32, 32))
        self.sound_btn.setFixedSize(32, 32)
        self.sound_btn.setToolTip(u"Toggle Sound Playback")
        self.sound_btn.clicked.connect(self.on_sound_btn_clicked)
        self.sound_btn.setFlat(True)

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

        # Control Bar Layout
        left_controls_layout = QtGui.QHBoxLayout()
        left_controls_layout.addWidget(self.options_btn)
        left_controls_layout.addWidget(self.sound_btn)

        middle_controls_layout = QtGui.QHBoxLayout()
        middle_controls_layout.addWidget(self.start_btn)
        middle_controls_layout.addWidget(self.vline)
        middle_controls_layout.addWidget(self.stop_btn)

        control_bar_layout = QtGui.QGridLayout()
        control_bar_layout.setContentsMargins(10, 0, 10, 0)
        control_bar_layout.setColumnStretch(0, 1)
        control_bar_layout.setColumnStretch(2, 1)
        control_bar_layout.addLayout(left_controls_layout, 0, 0, 0, 1, QtCore.Qt.AlignLeft)
        control_bar_layout.addLayout(middle_controls_layout, 0, 1, 1, 1, QtCore.Qt.AlignCenter)
        control_bar_layout.addWidget(self.reset_btn, 0, 2, 0, 1, QtCore.Qt.AlignRight)

        # Set Main Layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(0, 6, 0, 10)
        main_layout.addLayout(timer_bar_layout)
        main_layout.addWidget(self.central_list)
        main_layout.addLayout(control_bar_layout)
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

    def on_start_btn_clicked(self):
        if self.timer.isActive():
            pass
        else:
            self.central_list.clearContents()
            self.timer.start()
            self.start_btn.setText("Capture")

        self.stop_btn.setDisabled(False)

    def on_stop_btn_clicked(self):
        self.timer.stop()
        self.start_btn.setText(u"Start")
        self.stop_btn.setDisabled(True)

    def on_reset_btn_clicked(self):
        if self.timer.isActive():
            self.timer.stop()

        # Reset Timer and Frame counter
        if self.timer.offset:
            pass
        else:
            self.timer_label.setText("00:00:000")
            self.timer.time = QtCore.QTime()
            self.frame_counter_label.setNum(0)

        # Empty the table
        self.central_list.clear()

    def on_options_btn_clicked(self):
        if self.options_window.isVisible():
            self.options_window.hide()
        else:
            self.options_window.show()

    def on_sound_btn_clicked(self):
        pass

    # Other Actions

    def on_new_file_action_triggered(self):
        """
        Perform actions when 'new file" action is selected.
        :return: void
        """
        # Reset interface
        self.on_reset_btn_clicked()

        # Set new file
        self.file = ATFile()

    def on_open_file_action_triggered(self):
        pass

    def on_save_timing_action_triggered(self):
        pass

    def on_save_timing_as_action_triggered(self):
        pass

    def on_exit_app_action_triggered(self):
        self.close()

    def on_discard_changes_triggered(self):
        pass

    def on_show_on_timeline_triggered(self):
        pass

    def on_action_reset_window_size_triggered(self):
        self.resize(AnimationTimerUI.WIDTH, AnimationTimerUI.HEIGHT)

    def on_window_always_on_top_triggered(self):
        flags = self.windowFlags()
        if self.action_always_on_top.isChecked():
            flags |= QtCore.Qt.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self.show()
        else:
            flags &= ~QtCore.Qt.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self.show()

    # --

    def _center_window(self):
        """
        Set the window at the center of the screen.
        """
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _read_window_settings(self):
        """
        Read window settings.
        """
        settings = AnimationTimer.load_settings_file()

        settings.beginGroup("MainWindow")

        # Window screen position
        if settings.value("pos") is None:
            self._center_window()
        else:
            self.move(settings.value("pos", self.pos()))

        # Window sizing
        w = int(settings.value("width")) if settings.value("width") else AnimationTimerUI.WIDTH
        h = int(settings.value("height")) if settings.value("height") else AnimationTimerUI.HEIGHT
        self.resize(w, h)

        settings.endGroup()

        settings.beginGroup("Columns")

        self.action_column_interval.setChecked(bool_str(settings.value("interval", True)))
        self.action_column_note.setChecked(bool_str(settings.value("note", True)))

        settings.endGroup()

    def _write_window_settings(self):
        """
        Write updated window settings.
        """
        settings = AnimationTimer.load_settings_file()

        settings.beginGroup("MainWindow")

        settings.setValue("pos", self.pos())
        settings.setValue("always_on_top", self.action_always_on_top.isChecked())
        settings.setValue("width", self.width())
        settings.setValue("height", self.height())

        settings.endGroup()

        settings.beginGroup("Columns")

        settings.setValue("interval", self.action_column_interval.isChecked())
        settings.setValue("note", self.action_column_note.isChecked())

        settings.endGroup()

    # ---
    # Events

    def closeEvent(self, event):
        self._write_window_settings()
        # super(AnimationTimerUI, self).closeEvent(event)

    def moveEvent(self, event):
        self._write_window_settings()
        self.options_window.move_window()
        super(AnimationTimerUI, self).moveEvent(event)

    def resizeEvent(self, event):
        self.options_window.move_window()
        super(AnimationTimerUI, self).resizeEvent(event)

    def keyPressEvent(self, event):
        """
        This just accepts all keystrokes and does nothing with them
        so that they don't get propagated on to Maya's hotkeys
        """
        pass


class AnimationTimer(object):

    TITLE = u"Animation Timer"
    AUTHOR = u"Yann Schmidt"
    VERSION = u"1.4"
    USER_SCRIPT_DIR = pm.system.internalVar(userScriptDir=True)
    USER_PREFS_DIR = pm.system.internalVar(userPrefDir=True)
    ICON_DIR = pm.system.internalVar(userPrefDir=True) + 'icons/'

    def __init__(self):
        pass

    # ---

    @classmethod
    def load_settings_file(cls):
        return QtCore.QSettings(QtCore.QSettings.IniFormat,
                                QtCore.QSettings.UserScope,
                                u'yannschmidt.com/Animation Timer',
                                u'Animation Timer')

    # ---

    @classmethod
    def calculate_frame_length(cls, fps):
        """
        Calculate the length in millisec for 1 frame.
        - fps : int.
        @return int: millisec
        """
        frame_length = ceil(1000 / fps)
        return int(frame_length)

    @classmethod
    def calculate_frames(cls, ms, fps):
        """
        Calculate the current frame based on the elasped time and current
        fps.
        ms : int millisec
        fps: int value
        @return float frames
        """
        frames = fps * ms / 1000
        return frames

    @classmethod
    def calculate_time(cls, frame, fps, fmt="mm:ss:zzz"):
        """
        Calculte the time based on the frame and the current fps number
        :param frame: int
        :param fps: int
        :return: str
        """

        ms = AnimationTimer.calculate_time_ms(frame, fps)

        time = QtCore.QTime()
        time.setHMS(0,
                    time.addMSecs(ms).minute(),
                    time.addMSecs(ms).second(),
                    time.addMSecs(ms).msec())

        return time.toString(fmt)

    @classmethod
    def calculate_time_ms(cls, frame, fps):
        """
        Calculte the time based on the frame and the current fps number
        :param frame: int
        :param fps: int
        :return milliseconds: int
        """

        ms = ceil(float(frame) / float(fps) * 1000)
        ms = int(ms)

        return ms

    @classmethod
    def on_add_to_shelf(cls):
        """
        Add a program shortcut into a shelf.
        :return void
        """
        # Query the current selected shelf.
        g_shelf_top_level = pm.language.mel.eval('$temp1=$gShelfTopLevel')
        current_shelf = pm.shelfTabLayout(g_shelf_top_level, q=True, st=True)

        # Copy the shelf icon to current maya's icon dir.
        source = os.path.dirname(os.path.realpath(__file__)) + '/anim_timer_shelficon.png'

        try:
            shutil.copy(source, AnimationTimer.ICON_DIR)
        except:
            pass

        return pm.windows.shelfButton(
            p=current_shelf,
            rpt=True,
            image="pythonFamily.png",
            image1="anim_timer_shelficon.png",
            stp="python",
            l="Open Animation Timer v%s" % AnimationTimer.VERSION,
            command="import animationtimer; animationtimer.show()"
        )


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

        self.time = QtCore.QTime()
        self.offset = 0

        self.setSingleShot(False)
        self.elapsed_timer = QtCore.QElapsedTimer()

        # Connections
        self.timeout.connect(self.on_timer_changed)

    def start(self):
        """
        Start the 2 timers simultaneously.
        """
        super(ATTimer, self).start(1)
        self.elapsed_timer.start()

    def stop(self):
        """
        Stop the 2 timers simultaneously.
        """
        super(ATTimer, self).stop()
        self.elapsed_timer.invalidate()

    # ---

    @property
    def elapsed(self):
        if self.isActive():
            return self.elapsed_timer.elapsed()

    # ---

    def on_timer_changed(self):
        """
        Triggered every time the timer is timeout.
        """
        ms = self.elapsed

        # Offsets
        if self.offset:
            ms += self.offset

        # Timer
        self.time = QtCore.QTime()  # Reset
        self.time.setHMS(0,
                         self.time.addMSecs(ms).minute(),
                         self.time.addMSecs(ms).second(),
                         self.time.addMSecs(ms).msec())

        if self.time > QtCore.QTime(0, 59, 59, 999):
            self.stop()

        # Frame calculations


        # Update displays
        atui.timer_label.setText(self.time.toString("mm:ss:zzz"))


class ATCenterList(QtGui.QTableWidget):
    """
    Center List object.
    """
    def __init__(self, parent):
        super(ATCenterList, self).__init__(parent)

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setGridStyle(QtCore.Qt.DashLine)

        # Handle Shortcuts
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Connexions
        self.itemChanged.connect(self.on_content_changed)
        self.verticalHeader().sectionClicked.connect(self.on_vertical_header_clicked)

    def add(self, time, frame, note):
        """
        Append a new row to the table.
        """
        # Show the headers
        self._set_headers()

        # Create a new empty row
        self.insertRow(self.rowCount())

        # Create cells
        time_cell = QtGui.QTableWidgetItem(str(time))
        time_cell.setFlags(time_cell.flags() ^ QtCore.Qt.ItemIsEditable)
        time_cell.setTextAlignment(QtCore.Qt.AlignCenter)

        frame_cell = QtGui.QTableWidgetItem(str(frame))
        frame_cell.setFlags(frame_cell.flags() ^ QtCore.Qt.ItemIsEditable)
        frame_cell.setTextAlignment(QtCore.Qt.AlignCenter)

        interval_cell = QtGui.QTableWidgetItem()
        interval_cell.setFlags(interval_cell.flags() ^ QtCore.Qt.ItemIsEditable)
        interval_cell.setTextAlignment(QtCore.Qt.AlignCenter)

        note_cell = QtGui.QTableWidgetItem(str(note))
        note_cell.setToolTip(u"Double click to edit")
        note_cell.setTextAlignment(QtCore.Qt.AlignVCenter)

        # Set items
        self.setItem(self.rowCount(), 0, time_cell)
        self.setItem(self.rowCount(), 1, frame_cell)
        self.setItem(self.rowCount(), 2, interval_cell)
        self.setItem(self.rowCount(), 3, note_cell)

    def remove(self):
        """
        Remove one or more rows from the table.
        """
        pass

    def export_data(self):
        pass

    # ---

    def _set_headers(self):
        self.setHorizontalHeaderLabels(ATCenterList.column_list())

    # ---

    @classmethod
    def column_list(cls):
        return [
            'Time',
            'Frame',
            'Interval',
            'Note',
        ]

    # ---
    # Events

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            atui.on_start_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            atui.on_stop_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Backspace:
            # if len(self.selectionModel().selectedRows()) > 0:
            #     self.remove()
            # else:
            atui.on_reset_btn_clicked()
            event.accept()
        else:
            # make sure usual keys get dealt with
            super(ATCenterList, self).keyPressEvent(event)

    def focusOutEvent(self, *args, **kwargs):
        # When this widget loose the focus, stop the timer
        setting = AnimationTimer.load_settings_file()
        if setting.value("Preferences/stop_timer_on_out_focus", True):
            atui.timer.stop()

    # ---

    def on_content_changed(self, item):
        """

        """
        row = item.row()
        column = item.column()

    def on_vertical_header_clicked(self, logicalIndex):
        """
        By clicking on the row id, it start the playback from the current frame specified on this row.
        Each click restart the playback from this frame number.
        :param logicalIndex:
        :return:
        """
        pass
        # Get the frame number for the row
        # data = int(self.model.item(logicalIndex, 1).text())

        # Playback
        # cmds.play(state=False)
        # cmds.currentTime(data)
        # cmds.play(forward=True)


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

    fps_preset_list = [6, 12, 15, 24, 25, 30, 48, 50, 60]
    default = 24
    min_fps = 6
    max_fps = 120

    def __init__(self, parent=None):
        super(AnimationTimerOptions, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle(u"Options")
        self.setFixedSize(200, 500)
        self.setModal(False)

        self.move_window()

    # ---

    def move_window(self):
        x = self.parent.x() + self.parent.frameGeometry().width() + 20
        y = self.parent.y()

        self.move(x, y)


class AnimationTimerPreferences(QtGui.QDialog):

    def __init__(self, parent):
        super(AnimationTimerPreferences, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle(u"Preferences")
        self.setFixedSize(400, 350)

        self.create_layout()
        self.create_connections()

    def create_layout(self):
        pass

    def create_connections(self):
        pass

    # ---

    def on_accepted(self):
        pass

    def on_rejected(self):
        pass

    # ---

    def _change_current_tab(self):
        pass

    # ---

    def _read_pref_settings(self):
        pass

    def _write_pref_settings(self):
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
