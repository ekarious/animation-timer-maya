# -*- coding: utf-8 -*-

# Animation Timer
# Author: Yann Schmidt
# Maya 2014+

from PySide import QtCore, QtGui
from shiboken import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import maya.cmds as cmds

from math import ceil
import json

# Constants
TITLE = u"Animation Timer"
AUTHOR = u"Yann Schmidt"
VERSION = u"1.0"
USER_SCRIPT_DIR = cmds.internalVar(usd=True)
USER_PREFS_DIR = cmds.internalVar(upd=True)
DOCS_URL = 'http://yannschmidt.com/scripts/maya/animation-timer/docs/index'


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
    """
    Management of the main interface for Animation Timer.
    """

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
        self.file = None

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
        action_open.setStatusTip(u"Open existing Timing (.timing | .json)")
        action_open.setAutoRepeat(False)
        # action_open.setDisabled(True)
        action_open.triggered.connect(self.on_open_timing_triggered)

        # Action : Save
        action_save = QtGui.QAction(u"Save", self)
        action_save.setStatusTip(u"Save Timing")
        action_save.setAutoRepeat(False)
        action_save.triggered.connect(self.on_save_timing_triggered)

        # Action : Save As ...
        action_save_as = QtGui.QAction(u"Save As ...", self)
        action_save_as.setStatusTip(u"Save Timing as ...")
        action_save_as.setAutoRepeat(False)
        action_save_as.triggered.connect(self.on_save_as_timing_triggered)

        # Action : Recent Timing
        # TODO

        # Action : Exit Program
        action_exit = QtGui.QAction(u"Exit", self)
        action_exit.setStatusTip(u"Close this window")
        action_exit.triggered.connect(self.close)

        # -----

        # Action : Delete
        action_delete = QtGui.QAction(u"Delete row(s)", self)
        action_delete.setStatusTip(u"Delete selected row(s)")
        action_delete.triggered.connect(self.on_action_delete_clicked)

        # -----

        # Action : Show on Maya Timeline
        self.action_show_timeline = QtGui.QAction(u"Show on Timeline", self)
        self.action_show_timeline.setStatusTip(u"Show on Maya Timeline")
        self.action_show_timeline.setCheckable(True)
        self.action_show_timeline.setDisabled(True)

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
        userguideAction.triggered.connect(self.on_open_documentation_triggered)

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
        menu_edit.addAction(action_delete)

        # Maya menu
        # menu_maya = menubar.addMenu("Maya")
        # menu_maya.addAction(self.action_show_timeline)

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

        self.frames_description = QtGui.QLabel(
            "frames")
        self.frames_description.setStyleSheet("""
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
        self.frames = QtGui.QLabel()
        self.frames.setNum(0)

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
        timer_bar_layout.addWidget(self.frames_description, 1, 2, 1, 1,
                                   QtCore.Qt.AlignRight)

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
        # Set default always on top option.
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
        if self.timer.isActive():
            self.capture_data()
            self.central_list.horizontalHeader().show()
        else:
            self.central_list.model.clear()
            self.central_list.set_headers()
            # Get the update rate for the time based on the current fps.
            # Great for saving ressources.
            update_in_ms = AnimationTimer.calculate_frame_length(
                self.fps_window.current)
            self.timer.start(update_in_ms)

            self.start_btn.setText(u"Capture Frame")
            self.start_btn.setFixedWidth(150)

    def on_stop_btn_clicked(self):
        self.timer.stop()

        self.start_btn.setText(u"Start")
        self.start_btn.setFixedWidth(60)

    def on_reset_btn_clicked(self):
        if self.timer.isActive():
            self.timer.stop()

        # Reset timer and frames
        self.timer_visual.setText("00:00:000")
        self.timer.time = QtCore.QTime()
        self.frames.setText("0")

        # Reset Start btn
        self.start_btn.setText(u"Start")
        self.start_btn.setFixedWidth(60)

        # Empty the table
        self.central_list.clear()

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

    def on_open_documentation_triggered(self):
        url = QtCore.QUrl(DOCS_URL)
        return QtGui.QDesktopServices.openUrl(url)

    def on_open_timing_triggered(self):
        """
        Open a .timing or .json file and load its contents.
        """
        # Get the selected file
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self,
            'Open Timing',
            QtCore.QDir.homePath(),
            'Timing / Json Files (*.timing *.json)',
            '',
            QtGui.QFileDialog.DontUseNativeDialog)

        if not filename:
            return

        # Read the file, validate and import data
        data = AnimationTimer.read_timing_from_file(filename)
        if data is None:
            return

        AnimationTimer.import_data(data)

        # Set new file as the current file
        self.file = filename

    def on_save_timing_triggered(self):
        """
        Save a timing into a file.
        If file exists, do not ask for location
        """
        # If file currently not exists
        if self.file is None:
            dialog = AnimationTimer._open_save_window(self)

            if dialog.exec_():
                filename = dialog.selectedFiles()
            else:
                filename = None

            if not filename:
                return
            else:
                self.file = filename

        # Get all the data from the table + some magic
        data = self.central_list.get_dict()

        # Then save it !
        AnimationTimer.write_timing_to_file(self.file, data)

    def on_save_as_timing_triggered(self):
        """
        Save a timing into a file.
        Always ask for location before saving
        """
        dialog = AnimationTimer._open_save_window(self)

        if dialog.exec_():
            filename = dialog.selectedFiles()
        else:
            filename = None

        if not filename:
            return

        # Get all the data from the table + some magic
        data = self.central_list.get_dict()

        # Then save it !
        AnimationTimer.write_timing_to_file(filename, data)

        # Set newly save filename as current file
        self.file = filename

    def on_action_delete_clicked(self):
        """
        Delete current selected rows
        """
        self.central_list.remove()

    def capture_data(self):
        """
        Cature the current data from the timer and frames widget
        and save them as an instant 't' (snapshot).
        """
        timer = self.timer.get("mm:ss:zzz")
        frame = self.frames.text()

        self.central_list.add(timer, frame)

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

    def keyPressEvent(self, event):
        """
        This just accepts all keystrokes and does nothing with them
        so that they don't get propagated on to Maya's hotkeys
        """
        pass


class AnimationTimer(object):
    """
    Class for specific behevior operation.
    """
    def __init__(self):
        pass

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
    def calculate_frame_length(cls, fps):
        """
        Calculate the length in millisec for 1 frame.
        - fps : int.
        @return
        """
        frame_length = ceil(1000 / fps)
        return int(frame_length)

    @classmethod
    def write_timing_to_file(cls, filename, data):
        """
        Write a timing file with json.
        - filename : file to write into
        - data : dict to write in the file
        """
        # Add an item to the list at the top.
        d = {}
        d['plugin_name'] = TITLE
        d['fps'] = ui.fps_window.current

        data.insert(0, d)

        if isinstance(filename, list):
            filename = filename[0]

        # Save the data to a json file.
        if filename:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4, separators=(',', ': '))

    @classmethod
    def read_timing_from_file(cls, filename):
        """
        Open a file, read the content and show it into the  table
        - filename
        """
        with open(filename, "r") as f:
            data = json.load(f)

        try:
            if data[0].get('plugin_name') == TITLE and \
               data[0].get('fps'):
                return data
        except KeyError:
            return None

    @classmethod
    def import_data(cls, data):
        """
        Import data to software.
        """
        fps = data[0].get('fps')

        for x in range(1, len(data)):
            time = data[x].get('time')
            frame = data[x].get('frame')
            ui.central_list.add(time, frame)

        # Set fps
        ui.fps_window.current = int(fps)
        ui.fps.setText(str(fps) + " fps")

    @classmethod
    def _open_save_window(cls, parent):
        dialog = QtGui.QFileDialog(parent)
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('timing')
        dialog.setDirectory(QtCore.QDir.homePath())
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setNameFilter(
            'Timing File (*.timing);;Json File (*.json)')
        dialog.setWindowTitle("Save Timing as ...")
        dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog)

        return dialog


class Timer(QtCore.QTimer):
    """
    This can be quite difficult to understand.
    QTimer is here for display purpose and better user interaction.
    QElapsedTimer is here for calculation of elapsed time for the program.
    """
    def __init__(self, parent):
        super(Timer, self).__init__(parent)

        self.is_stop_needed = False
        self.time = QtCore.QTime()

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
        self.is_stop_needed = False

    def elapsed(self):
        """
        Get the elapsed time between the start.
        """
        if self.isTimerValid():
            return self.qelapsedtimer.elapsed()

    def hasExpired(self, timeout):
        """
        timeout need to be an qint64 type of int.
        """
        self.qelapsedtimer.hasExpired(timeout)

    def auto_stop_at_time(self):
        """
        Auto Stop the timer at a choosen time if needed.
        """
        # Get current auto stop state.
        auto_stop = ui.auto_stop_window.current

        if isinstance(auto_stop, QtCore.QTime):
            if self.time >= auto_stop:
                self.is_stop_needed = True
        else:
            pass

    def auto_stop_at_frame(self):
        """
        Auto Stop the timer at a choosen frame if needed.
        """
        # Get current auto stop state.
        auto_stop = ui.auto_stop_window.current

        if isinstance(auto_stop, int):
            if int(ui.frames.text()) >= auto_stop:
                self.is_stop_needed = True
        else:
            pass

    def get(self, format):
        """
        Return the timer with the specified format
        """
        return self.time.toString(format)

    # SLOTS
    # -----

    def on_timer_changed(self):
        """Function triggered every time the timer's timeout"""
        # Check for AutoStop
        if ui.auto_stop_window.current is not None:
            self.auto_stop_at_time()
            self.auto_stop_at_frame()

        # Set the default values.
        ms = self.elapsed()

        frames_amount = AnimationTimer.calculate_frames(
            ms,
            ui.fps_window.current)

        # Check if auto stop needed.
        if self.is_stop_needed is True:
            self.stop()

        # Get the different parts of the time and populate the QTime object.
        self.time = QtCore.QTime()  # Reset the timer before setting the time.
        self.time.setHMS(0,
                         self.time.addMSecs(ms).minute(),
                         self.time.addMSecs(ms).second(),
                         self.time.addMSecs(ms).msec())

        # Security
        # Stop the timer is QTime is about to be an hour long.
        if self.time > QtCore.QTime(0, 59, 59, 999):
            self.stop()

        # Update the Display with the QTime object into a specific format.
        ui.timer_visual.setText(self.time.toString("mm:ss:zzz"))

        # Update the frames count.
        ui.frames.setNum(int(frames_amount))


class CenterList(QtGui.QTableView):

    def __init__(self, parent=None):
        super(CenterList, self).__init__(parent)

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setGridStyle(QtCore.Qt.DashLine)

        # Handle shortcuts
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Model
        self.model = QtGui.QStandardItemModel(self)

        self.setModel(self.model)

    def add(self, time, frame):
        """
        Add a row to the table

        Item contents:
        - Time
        - Frame Number
        """
        self.set_headers()

        row0 = QtGui.QStandardItem(str(time))
        row0.setTextAlignment(QtCore.Qt.AlignCenter)

        row1 = QtGui.QStandardItem(str(frame))
        row1.setTextAlignment(QtCore.Qt.AlignCenter)

        l = [row0, row1]

        self.model.appendRow(l)

    def remove(self):
        """
        Remove selected items.
        """
        i = self.selectionModel().selectedRows()
        for x in i:
            self.model.removeRow(x.row())

    def clear(self):
        """
        Clear the whole list.
        """
        self.model.clear()
        self.horizontalHeader().hide()

    def set_headers(self):
        """
        Set the headers for the list.
        """
        headers = []
        headers.append(u"Time")
        headers.append(u"Frames")

        self.model.setHorizontalHeaderLabels(headers)

    def get_dict(self):
        """
        Create a dict of items ()
        """
        row_count = self.model.rowCount()

        l = []

        # For each line...
        for row in range(0, row_count):

            # Get data from the columns...
            d = {}
            d["time"] = self.model.item(row, 0).text()
            d["frame"] = self.model.item(row, 1).text()

            l.append(d)

        return l

    # EVENTS
    # ------

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            ui.on_start_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            ui.on_stop_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Backspace:
            if len(self.selectionModel().selectedRows()) > 0:
                self.remove()
            else:
                ui.on_reset_btn_clicked()

            event.accept()
        else:
            # make sure usual keys get dealt with
            super(CenterList, self).keyPressEvent(event)


class FramePerSecondWindow(QtGui.QDialog):

    fps_preset_list = [6, 12, 15, 24, 25, 30, 48, 50, 60]
    default = 24

    def __init__(self, parent=None):
        super(FramePerSecondWindow, self).__init__(parent)

        self.current = FramePerSecondWindow.default

        self.setWindowTitle(u"Choose FPS")
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
            self.current = self.time_edit.time()
            ui.timing_option_btn.setText(
                "Auto Stop at " + self.time_edit.time().toString("mm:ss:zzz"))

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
