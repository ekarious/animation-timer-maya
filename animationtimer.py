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
VERSION = u"0.1d"
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
        self.resize(600, 370)
        self.setMinimumSize(400, 300)
        self.setMaximumWidth(600)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.central_widget = QtGui.QWidget()
        self.setCentralWidget(self.central_widget)

        self.create_menu()
        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.settings = AnimationTimerUI._load_settings_file()
        self.settings.setFallbacksEnabled(False)
        self._read_window_settings()

        self.populate()

        self.timer = Timer(self)

        # Special Windows
        self.fps_window = FramePerSecondWindow(self)
        self.auto_stop_window = AutoStopWindow(self)

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

        # Action : Show on Maya Timeline
        self.action_show_timeline = QtGui.QAction(u"Show on Timeline", self)
        self.action_show_timeline.setStatusTip(u"Show on Maya Timeline")
        self.action_show_timeline.setCheckable(True)

        # -----

        # Action : Always on Top
        self.action_always_on_top = QtGui.QAction(u"Always on Top", self)
        self.action_always_on_top.setCheckable(True)
        self.action_always_on_top.triggered.connect(
            self.on_window_always_on_top_triggered)

        # -----

        # Action : Documentations
        userguideAction = QtGui.QAction(u"Documentation", self)
        userguideAction.setStatusTip(u"Open the Documentation"
                                     " inside a web browser")

        # Action : About Window
        action_about = QtGui.QAction(u"About", self)
        action_about.setStatusTip(u"About Animation Timer")
        action_about.setAutoRepeat(False)
        action_about.triggered.connect(self.open_about_window)

        # Create the menu
        menubar = self.menuBar()

        # File menu
        menu_file = menubar.addMenu("File")
        menu_file.setTearOffEnabled(True)
        menu_file.addAction(action_open)
        menu_file.addSeparator()
        menu_file.addAction(action_save)
        menu_file.addAction(action_save_as)
        menu_file.addSeparator()
        menu_file.addAction(action_exit)

        # Edit menu
        menu_edit = menubar.addMenu("Edit")
        menu_edit.setTearOffEnabled(True)
        menu_edit.addAction(action_undo)
        menu_edit.addAction(action_redo)
        menu_edit.addSeparator()
        menu_edit.addAction(action_copy)
        menu_edit.addAction(action_cut)
        menu_edit.addAction(action_paste)
        menu_edit.addSeparator()
        menu_edit.addAction(action_select_all)
        menu_edit.addAction(action_delete)

        # Maya menu
        menu_maya = menubar.addMenu("Maya")
        menu_maya.addAction(self.action_show_timeline)

        # Window menu
        menu_window = menubar.addMenu("Window")
        menu_window.addAction(self.action_always_on_top)

        # Help menu
        menu_help = menubar.addMenu("Help")
        menu_help.addAction(userguideAction)
        menu_help.addAction(action_about)

    def create_controls(self):
        """
        Create the controls
        """
        # Timer
        self.font_timer = QtGui.QFont()
        self.font_timer.setPixelSize(36)

        self.timer_visual = QtGui.QLabel("00:00:000")
        self.timer_visual.setFont(self.font_timer)
        self.timer_visual.setFixedHeight(60)
        self.timer_visual.setStyleSheet("""
                                             margin-top:-10px;
                                             """)

        self.timer_description = QtGui.QLabel(
            "min : sec : millisec")
        self.timer_description.setStyleSheet("""
                                             margin-top:15px;
                                             color:#757575;
                                             font-style:italic;
                                             """)

        # Center Area
        self.central_list = CenterList()

        # Buttons
        self.font_start = QtGui.QFont()
        self.font_start.setPixelSize(18)

        self.font_secondary_buttons = QtGui.QFont()
        self.font_secondary_buttons.setPixelSize(14)

        self.start_btn = QtGui.QPushButton(u"Start")
        self.start_btn.setFixedSize(60, 35)
        self.start_btn.setFont(self.font_start)
        self.start_btn.setDefault(True)

        self.stop_btn = QtGui.QPushButton(u"Stop")
        self.stop_btn.setFixedSize(50, 30)
        self.stop_btn.setFont(self.font_secondary_buttons)

        self.reset_btn = QtGui.QPushButton(u"Reset")
        self.reset_btn.setFixedSize(50, 30)
        self.reset_btn.setFont(self.font_secondary_buttons)

        self.timing_option_btn = QtGui.QPushButton(u"No Auto Stop")
        self.timing_option_btn.setFlat(True)

        # Labels
        self.frames = QtGui.QLabel("0")

        # ComboBox
        self.fps = QtGui.QPushButton("24 fps")
        self.fps.setFlat(True)

    def create_layout(self):

        # Buttons
        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.setAlignment(QtCore.Qt.AlignCenter)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.reset_btn)

        # Controls layer
        controls_layer = QtGui.QGridLayout()
        controls_layer.setContentsMargins(10, 0, 10, 0)
        controls_layer.addWidget(self.fps, 0, 0, 1, 1, QtCore.Qt.AlignLeft)
        controls_layer.addLayout(buttons_layout, 0, 1, 0, 1)
        controls_layer.addWidget(self.timing_option_btn, 0, 2, 1, 1,
                                 QtCore.Qt.AlignRight)

        # Timer bar layer
        timer_bar_layout = QtGui.QGridLayout()
        timer_bar_layout.setContentsMargins(10, 0, 10, 0)
        timer_bar_layout.setColumnStretch(0, 1)
        timer_bar_layout.setColumnStretch(2, 1)
        timer_bar_layout.addWidget(self.timer_visual, 0, 1, 0, 1)
        timer_bar_layout.addWidget(self.frames, 0, 2, 2, 1,
                                   QtCore.Qt.AlignRight)
        timer_bar_layout.addWidget(self.timer_description, 1, 1, 1, 1,
                                   QtCore.Qt.AlignCenter)

        # Set the Main Layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(0, 6, 0, 10)
        main_layout.addLayout(timer_bar_layout)
        main_layout.addWidget(self.central_list)
        main_layout.addLayout(controls_layer)

        self.central_widget.setLayout(main_layout)

    def create_connections(self):
        self.fps.clicked.connect(self.open_fps_window)
        self.timing_option_btn.clicked.connect(self.open_auto_stop_window)

        self.start_btn.clicked.connect(self.on_start_btn_clicked)
        self.stop_btn.clicked.connect(self.on_stop_btn_clicked)
        self.reset_btn.clicked.connect(self.on_reset_btn_clicked)

    def populate(self):
        """
        Populate the Program at first launch
        """
        if self.action_always_on_top.isChecked():
            self.on_window_always_on_top_triggered()

    def open_fps_window(self):
        """
        Can choose the fps in a separate window
        """
        current_list = self.fps.text().split(' ')
        if int(current_list[0]) in FramePerSecondWindow.fps_preset_list:
            self.fps_window.radio_preset.setChecked(True)
            n = self.fps_window.fps_combobox.findText(current_list[0])
            self.fps_window.fps_combobox.setCurrentIndex(n)
            self.fps_window.on_preset_selected()
        else:
            self.fps_window.radio_custom.setChecked(True)
            self.fps_window.fps_custom_spinbox.setValue(int(current_list[0]))
            self.fps_window.on_custom_selected()

        self.fps_window.exec_()

    def open_auto_stop_window(self):
        """
        Can choose auto stop condition in a new window
        """
        self.auto_stop_window.exec_()

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

    # SLOTS
    # -----

    def on_start_btn_clicked(self):
        print("Start btn clicked.")
        self.timer.start()

    def on_stop_btn_clicked(self):
        print("Stop btn clicked.")
        self.timer.stop()

    def on_reset_btn_clicked(self):
        print("Reset btn clicked.")

    def on_maya_show_timeline_triggered(self):
        print("Show on timeline checkbox triggered.")

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

    # Others

    def center_window(self):
        """
        Set the window at the center of the screen
        """
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @classmethod
    def _load_settings_file(cls):
        return QtCore.QSettings(QtCore.QSettings.IniFormat,
                                QtCore.QSettings.UserScope,
                                u'yannschmidt.com/Animation Timer',
                                u'Animation Timer')

    def _read_window_settings(self):
        """
        Read windows attributes from settings.
        """
        settings = self.settings

        settings.beginGroup("mainwindow")

        # Read data
        if settings.value("pos") is None:
            self.center_window()
        else:
            self.move(settings.value("pos", self.pos()))

        self.action_always_on_top.setChecked(
            _str_to_bool(settings.value("always_on_top", True)))

        settings.endGroup()

    def _write_window_settings(self):
        """
        Called when window moved or closed
        """
        settings = self.settings

        settings.beginGroup("MainWindow")

        # Write data
        settings.setValue("pos", self.pos())
        settings.setValue(
            "always_on_top",
            self.action_always_on_top.isChecked())

        settings.endGroup()

    # Overloadding events
    # -------------------

    def closeEvent(self, event):
        # Save window attributes settings on close
        self._write_window_settings()

    def moveEvent(self, event):
        # Save window attributes settings on move
        self._write_window_settings()


class AnimationTimer(object):
    pass


class Timer(QtCore.QTimer):
    """
    This can be quite difficult to understand.
    QTimer is here for display purpose and better user interaction.
    QElapsedTimer is here for calculation of elapsed time for the program.
    """
    def __init__(self, parent):
        super(Timer, self).__init__(parent)

        self.setSingleShot(False)
        self.qelapsedtimer = QtCore.QElapsedTimer()

        self.timeout.connect(self.on_timer_changed)

    def isTimerActive(self):
        super(Timer, self).isActive()

    def isTimerValid(self):
        return self.qelapsedtimer.isValid()

    def start(self, msec=1):
        """
        Start timers
        """
        super(Timer, self).start(msec)
        self.qelapsedtimer.start()

    def stop(self):
        """
        Stop QTimer
        Invalidate QElapsedTimer (security)
        """
        super(Timer, self).stop()
        self.qelapsedtimer.invalidate()

    def elasped(self):
        """
        Get the elasped time between the start.
        """
        if self.isTimerValid():
            return self.qelapsedtimer.elasped()

    def hasExpired(self, timeout):
        """
        timeout need to be an qint64 type of int.
        """
        self.qelapsedtimer.hasExpired(timeout)

    # SLOTS
    # -----

    def on_timer_changed(self):
        """Function triggered every time the timer timeout"""
        ui.timer_visual.setText(self.elapsed())


class CenterList(QtGui.QListView):

    def __init__(self, parent=None):
        super(CenterList, self).__init__(parent)

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        # Model
        self.model = QtGui.QStandardItemModel(self)

        # First try to set Headers for the list
        headers = []
        headers.append(u"ID")
        headers.append(u"Time")
        headers.append(u"Frames")

        self.model.setHorizontalHeaderLabels(headers)
        self.model.setColumnCount(3)

        self.setModel(self.model)

    def add(self, item):
        """
        Add a item to the list

        Item contents:
        - ID
        - Time
        - Frame Number
        """
        pass

    def remove(self, items):
        """
        Remove selected items.
        """
        i = self.selectedIndexes()
        for x in i:
            self.model.removeRow(x.row())

    def clear(self):
        """
        Clear the whole list.
        """
        self.model.clear()


class FramePerSecondWindow(QtGui.QDialog):

    fps_preset_list = [6, 12, 15, 24, 25, 30, 48, 50, 60]
    default = 24

    def __init__(self, parent=None):
        super(FramePerSecondWindow, self).__init__(parent)

        self.current = FramePerSecondWindow.default

        self.setWindowTitle(u"Chose FPS")
        self.setFixedSize(250, 150)

        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.populate()

    def create_controls(self):
        self.radio_preset = QtGui.QRadioButton(u"Presets")
        self.radio_preset.setFixedWidth(80)
        self.radio_preset.setStyleSheet("""
                                        margin-left:15px;
                                        """)

        self.radio_custom = QtGui.QRadioButton(u"Custom")
        self.radio_custom.setFixedWidth(80)
        self.radio_custom.setStyleSheet("""
                                        margin-left:15px;
                                        """)

        self.fps_combobox = QtGui.QComboBox()
        self.fps_combobox.setFixedWidth(100)

        self.fps_label = QtGui.QLabel(u"fps")
        self.custom_fps_label = QtGui.QLabel(u"fps")

        self.separator = QtGui.QFrame()
        self.separator.setFrameShape(QtGui.QFrame.HLine)
        self.separator.setFrameShadow(QtGui.QFrame.Sunken)

        self.fps_custom_spinbox = QtGui.QSpinBox()
        self.fps_custom_spinbox.setRange(6, 120)
        self.fps_custom_spinbox.setFixedWidth(100)
        self.fps_custom_spinbox.setButtonSymbols(
            QtGui.QAbstractSpinBox.NoButtons)
        self.fps_custom_spinbox.setSingleStep(2)

        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                                 QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)

    def create_layout(self):

        # Presets FPS layout
        preset_layout = QtGui.QHBoxLayout()
        preset_layout.addWidget(self.radio_preset)
        preset_layout.addWidget(self.fps_combobox)
        preset_layout.addWidget(self.fps_label)

        # Custom FPS layout
        custom_layout = QtGui.QHBoxLayout()
        custom_layout.addWidget(self.radio_custom)
        custom_layout.addWidget(self.fps_custom_spinbox)
        custom_layout.addWidget(self.custom_fps_label)

        # Main layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(preset_layout)
        main_layout.addWidget(self.separator)
        main_layout.addLayout(custom_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def create_connections(self):
        self.radio_preset.clicked.connect(self.on_preset_selected)
        self.radio_custom.clicked.connect(self.on_custom_selected)

    def populate(self):
        """
        If the current fps is not in the preset list, set as custom
        else it is a preset.
        """
        # Set the list
        for x in FramePerSecondWindow.fps_preset_list:
            self.fps_combobox.addItem(str(x))

        # Set to default preset and disabled custom at start
        self.radio_preset.setChecked(True)
        n = self.fps_combobox.findText(str(self.current))
        self.fps_combobox.setCurrentIndex(n)
        self.on_preset_selected()

    # SLOTS
    # -----

    def on_preset_selected(self):
        self.fps_combobox.setEnabled(True)
        self.fps_custom_spinbox.setEnabled(False)

        self.fps_label.setStyleSheet("""
                                     color:#C8C8C8;
                                     """)

        self.radio_preset.setStyleSheet("""
                                     color:#C8C8C8;
                                     margin-left:15px;
                                     """)

        self.radio_custom.setStyleSheet("""
                                     color:#707070;
                                     margin-left:15px;
                                     """)

        self.custom_fps_label.setStyleSheet("""
                                     color:#707070;
                                     """)

    def on_custom_selected(self):
        self.fps_combobox.setEnabled(False)
        self.fps_custom_spinbox.setEnabled(True)

        self.fps_label.setStyleSheet("""
                                     color:#707070;
                                     """)

        self.custom_fps_label.setStyleSheet("""
                                     color:#C8C8C8;
                                     """)

        self.radio_preset.setStyleSheet("""
                                     color:#707070;
                                     margin-left:15px;
                                     """)

        self.radio_custom.setStyleSheet("""
                                     color:#C8C8C8;
                                     margin-left:15px;
                                     """)

    # ---

    def on_accepted(self):
        if self.radio_preset.isChecked():
            value = int(self.fps_combobox.currentText())

        if self.radio_custom.isChecked():
            value = int(self.fps_custom_spinbox.value())

        self.current = value
        ui.fps.setText(str(self.current) + " fps")
        return self.accept()

    def on_rejected(self):
        return self.reject()


class AutoStopWindow(QtGui.QDialog):

    def __init__(self, parent=None):
        super(AutoStopWindow, self).__init__(parent)

        self.current = None

        self.setWindowTitle(u"Auto Stop Timer")
        self.setFixedSize(250, 200)

        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.populate()

    def create_controls(self):
        self.radio_none = QtGui.QRadioButton(u"Disabled")
        self.radio_none.setFixedWidth(120)
        self.radio_none.setStyleSheet("""
                                      margin-left:28px;
                                      """)

        self.radio_time = QtGui.QRadioButton(u"Time")
        self.radio_time.setFixedWidth(80)
        self.radio_time.setStyleSheet("""
                                      margin-left:15px;
                                      """)

        self.radio_frames = QtGui.QRadioButton(u"Frame")
        self.radio_frames.setFixedWidth(80)
        self.radio_frames.setStyleSheet("""
                                        margin-left:15px;
                                        """)

        self.separator = QtGui.QFrame()
        self.separator.setFrameShape(QtGui.QFrame.HLine)
        self.separator.setFrameShadow(QtGui.QFrame.Sunken)

        self.separator2 = QtGui.QFrame()
        self.separator2.setFrameShape(QtGui.QFrame.HLine)
        self.separator2.setFrameShadow(QtGui.QFrame.Sunken)

        self.time_edit = QtGui.QTimeEdit()
        self.time_edit.setFixedWidth(100)
        self.time_edit.setMinimumTime(QtCore.QTime(0, 0, 1, 0))
        self.time_edit.setMaximumTime(QtCore.QTime(0, 60, 00, 000))
        self.time_edit.setDisplayFormat("mm:ss:zzz")

        self.frames_spinbox = QtGui.QSpinBox()
        self.frames_spinbox.setMinimum(1)
        self.frames_spinbox.setFixedWidth(100)
        self.frames_spinbox.setSingleStep(1)
        self.frames_spinbox.setMaximum(99999)

        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                                 QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)

    def create_layout(self):

        # Time layout
        preset_layout = QtGui.QHBoxLayout()
        preset_layout.addWidget(self.radio_time)
        preset_layout.addWidget(self.time_edit)

        # Frame layout
        custom_layout = QtGui.QHBoxLayout()
        custom_layout.addWidget(self.radio_frames)
        custom_layout.addWidget(self.frames_spinbox)

        # Main layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.radio_none)
        main_layout.addWidget(self.separator2)
        main_layout.addLayout(preset_layout)
        main_layout.addWidget(self.separator)
        main_layout.addLayout(custom_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def create_connections(self):
        self.radio_none.clicked.connect(self.on_disabled_selected)
        self.radio_time.clicked.connect(self.on_time_selected)
        self.radio_frames.clicked.connect(self.on_frame_selected)

    def populate(self):
        """Set to disabled by default"""
        self.radio_none.setChecked(True)
        self.on_disabled_selected()

    # SLOTS
    # -----

    def on_disabled_selected(self):
        self.time_edit.setEnabled(False)
        self.frames_spinbox.setEnabled(False)

        self.radio_none.setStyleSheet("""
                                      color:#C8C8C8;
                                      margin-left:28px;
                                      """)

        self.radio_frames.setStyleSheet("""
                                        color:#707070;
                                        margin-left:15px;
                                        """)

        self.radio_time.setStyleSheet("""
                                        color:#707070;
                                        margin-left:15px;
                                        """)

        self.time_edit.setStyleSheet("""
                                     color:#707070;
                                     """)

        self.frames_spinbox.setStyleSheet("""
                                     color:#707070;
                                     """)

    def on_time_selected(self):
        self.time_edit.setEnabled(True)
        self.frames_spinbox.setEnabled(False)

        self.radio_none.setStyleSheet("""
                                      color:#707070;
                                      margin-left:28px;
                                      """)

        self.radio_frames.setStyleSheet("""
                                        color:#707070;
                                        margin-left:15px;
                                        """)

        self.radio_time.setStyleSheet("""
                                        color:#C8C8C8;
                                        margin-left:15px;
                                        """)

        self.time_edit.setStyleSheet("""
                                     color:#C8C8C8;
                                     """)

        self.frames_spinbox.setStyleSheet("""
                                     color:#707070;
                                     """)

    def on_frame_selected(self):
        self.time_edit.setEnabled(False)
        self.frames_spinbox.setEnabled(True)

        self.radio_none.setStyleSheet("""
                                      color:#707070;
                                      margin-left:28px;
                                      """)

        self.radio_frames.setStyleSheet("""
                                        color:#C8C8C8;
                                        margin-left:15px;
                                        """)

        self.radio_time.setStyleSheet("""
                                        color:#707070;
                                        margin-left:15px;
                                        """)

        self.time_edit.setStyleSheet("""
                                     color:#707070;
                                     """)

        self.frames_spinbox.setStyleSheet("""
                                     color:#C8C8C8;
                                     """)

    # Others

    def on_accepted(self):
        """
        self.current can have 3 types of value:
        - None
        - Time : QTime object
        - Frames : integer
        """
        if self.radio_none.isChecked():
            self.current = None
            ui.timing_option_btn.setText("No Auto Stop")

        if self.radio_time.isChecked():
            self.current = self.time_edit.time().toString("mm:ss:zzz")
            ui.timing_option_btn.setText(
                "Auto Stop at " + self.current)

        if self.radio_frames.isChecked():
            self.current = int(self.frames_spinbox.value())
            frame_text = ' frame' if str(self.current) == '1' else ' frames'
            ui.timing_option_btn.setText(
                "Auto Stop at " + str(self.current) + frame_text)

        return self.accept()

    def on_rejected(self):
        return self.reject()


if __name__ == "__main__":

    try:
        ui.close()
    except:
        pass

    ui = AnimationTimerUI()
    ui.show()
