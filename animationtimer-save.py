# -*- coding: utf-8 -*-

# Animation Timer
# Author: Yann Schmidt
# Maya 2014+

from PySide import QtCore, QtGui
from shiboken import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

from math import ceil
import json

# Constants
TITLE = u"Animation Timer"
AUTHOR = u"Yann Schmidt"
VERSION = u"1.3"
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

        self.settings = AnimationTimerUI.load_settings_file()
        self.settings.setFallbacksEnabled(False)
        self._read_window_settings()

        self.timer = Timer(self)
        self.file = None
        self.data = None
        self.data_changed = False
        self.recent_timings = RecentTiming(self)

        # Special Windows
        self.fps_window = FramePerSecondWindow(self)
        self.auto_stop_window = AutoStopWindow(self)
        self.preference_window = AnimationTimerPreferences(self)

        self.populate()

    def create_menu(self):
        """
        Create the main menu and associate actions
        """
        # Action : New Timing
        action_new = QtGui.QAction(u"New Timing", self)
        action_new.setStatusTip(u"Create a new Timing")
        action_new.setAutoRepeat(False)
        action_new.triggered.connect(self.on_new_timing_triggered)

        # Action : Open Timing
        action_open = QtGui.QAction(u"Open Timing", self)
        action_open.setStatusTip(u"Open existing Timing (.timing | .json)")
        action_open.setAutoRepeat(False)
        action_open.triggered.connect(self.on_open_timing_triggered)

        # ---

        # Action : Current Timing menu
        current_timing = QtGui.QMenu(
            u'Current Timing', self
        )

        # Action : Current Timing : Discard and reload
        self.current_timing_reload = QtGui.QAction(
            u"Discard changes",
            self)
        self.current_timing_reload.setStatusTip(
            u"Discard all changes made since you opened/created that file.")
        self.current_timing_reload.setAutoRepeat(False)
        self.current_timing_reload.triggered.connect(
            self.on_discard_changes_n_reload)

        # Action : Recent Timing
        self.recent_timing_menu = QtGui.QMenu(
            u'Recent Timings', self
        )

        self.empty_action = QtGui.QAction(u'Empty', self)
        self.empty_action.setDisabled(True)

        # ---

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

        # Action : Exit Program
        action_exit = QtGui.QAction(u"Exit", self)
        action_exit.setStatusTip(u"Close this window")
        action_exit.triggered.connect(self.on_close_app)

        # -----

        # Action : Delete
        action_delete = QtGui.QAction(u"Delete row(s)", self)
        action_delete.setStatusTip(u"Delete selected row(s)")
        action_delete.triggered.connect(self.on_action_delete_clicked)

        # Action : Preference Window
        action_preferences = QtGui.QAction(u"Preferences", self)
        action_preferences.setStatusTip(u"Open the preferences window")
        action_preferences.triggered.connect(self.open_preference_window)

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

        # Action : Add to Shelf
        shelficon_action = QtGui.QAction(u"Add to Shelf", self)
        shelficon_action.setStatusTip(u"Add a shortcut to the selected shelf.")
        shelficon_action.triggered.connect(self.on_add_to_shelf)

        # Action : About Window
        action_about = QtGui.QAction(u"About", self)
        action_about.setStatusTip(u"About Animation Timer")
        action_about.setAutoRepeat(False)
        action_about.triggered.connect(self.open_about_window)

        # Create the menu
        menubar = self.menuBar()

        # File menu
        self.menu_file = menubar.addMenu("File")
        self.menu_file.setTearOffEnabled(True)
        self.menu_file.addAction(action_new)
        self.menu_file.addAction(action_open)
        self.menu_file.addSeparator()
        self.menu_file.addMenu(current_timing)

        current_timing.addAction(self.current_timing_reload)
        self.menu_file.addMenu(self.recent_timing_menu)  # Children added later.
        self.menu_file.addSeparator()
        self.menu_file.addAction(action_save)
        self.menu_file.addAction(action_save_as)
        self.menu_file.addSeparator()
        self.menu_file.addAction(action_exit)

        # Edit menu
        menu_edit = menubar.addMenu("Edit")
        menu_edit.setTearOffEnabled(True)
        menu_edit.addAction(action_delete)
        menu_edit.addSeparator()
        menu_edit.addAction(action_preferences)

        # Maya menu
        # menu_maya = menubar.addMenu("Maya")
        # menu_maya.addAction(self.action_show_timeline)

        # Window menu
        menu_window = menubar.addMenu("Window")
        menu_window.addAction(self.action_always_on_top)

        # Help menu
        menu_help = menubar.addMenu("Help")
        menu_help.addAction(userguideAction)
        menu_help.addAction(shelficon_action)
        menu_help.addSeparator()
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
        self.fps = QtGui.QPushButton()
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

        self.central_list.model.rowsInserted.connect(self.on_content_changed)
        self.central_list.model.rowsRemoved.connect(self.on_content_changed)

    def populate(self):
        """
        Populate the Program at first launch
        """
        # Set default always on top option.
        if self.action_always_on_top.isChecked():
            self.on_window_always_on_top_triggered()

        self.change_window_title()
        self.current_timing_reload.setDisabled(True)

        # Set default fps
        self.fps.setText(
            self.settings.value(
                "Preferences/default_fps",
                str(FramePerSecondWindow.default)) + ' fps')

        # Genarate recent timings menu
        self._generate_recent_timing_menu()

        # if checked in option, auto load last work
        if _str_to_bool(self.settings.value("Preferences/auto_load_last_timing")):
            filename = self.recent_timings.read(0)
            self.load_timing(filename)

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

    def open_preference_window(self):
        """
        Can choose auto stop condition in a new window
        """
        self.preference_window.exec_()

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

    def on_close_app(self):

        if self.data_changed:
            message = u'The timing your are working on has changes.'
            message += u'<p>Do you want to save it before exiting ?<p>'

            window = QtGui.QMessageBox.question(
                self,
                u'Timing has changed !',
                message,
                QtGui.QMessageBox.Save,
                QtGui.QMessageBox.Close
            )

            if window == QtGui.QMessageBox.Save:
                self.on_save_timing_triggered()

        # Close the app
        self.close()

    def on_content_changed(self):

        # If data is none
        if self.data is None:
            if self.central_list.row_count() == 0:
                self.data_changed = False
            else:
                self.data_changed = True

        # If not None (a file was opened)
        else:
            if self.central_list.get_items() == self.data:
                self.data_changed = False
            else:
                self.data_changed = True

        self.change_window_title()
        if self.data_changed:
            self.current_timing_reload.setDisabled(False)
        else:
            self.current_timing_reload.setDisabled(True)

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

    def on_discard_changes_n_reload(self):
        """
        Discard all changes and reload base data.
        - Base data can be an empty sheet or a previously loaded file.
        """
        self.on_reset_btn_clicked()

        if self.data is not None:
            self.import_data(self.data)

        self.data_changed = False
        self.change_window_title()

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

    def on_add_to_shelf(self):
        """
        Add the script to a shelf icon
        """
        # Query the current selected Shelf
        gShelfTopLevel = mel.eval('$temp1=$gShelfTopLevel')
        current_shelf = cmds.tabLayout(gShelfTopLevel, q=True, st=True)

        # Create the shelf button
        return cmds.shelfButton(
            p=current_shelf,
            rpt=True,
            image="pythonFamily.png",
            image1="anim_timer_shelficon.png",
            stp="python",
            l="Open Animation Timer v%s" % VERSION,
            command="import animationtimer; animationtimer.show()"
        )

    def on_new_timing_triggered(self):
        """
        When triggered, "create" a new timing.
        It is just a blank canvas, with no file loaded.
        """
        self.file = None
        self.data = None
        self.data_changed = False
        self.on_reset_btn_clicked()
        self.change_window_title()

    def on_open_timing_triggered(self):
        """
        Open a .timing or .json file and load its contents.
        ---
        Save the filename
        Save the file data to see what changes afterward.
        """
        # Get the selected file
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self,
            'Open Timing',
            self.switch_filedialog_dir(),
            'Timing / Json Files (*.timing *.json)',
            '',
            QtGui.QFileDialog.DontUseNativeDialog)

        if not filename:
            return None

        self.load_timing(filename)

    def on_save_timing_triggered(self):
        """
        Save a timing into a file.
        If file exists, do not ask for location
        """
        # Just in case
        self.timer.stop()

        # If file currently not exists
        if self.file is None:
            dialog = AnimationTimer._open_save_window(self)

            if dialog.exec_():
                filename = dialog.selectedFiles()
            else:
                return

            self.file = QtCore.QDir(filename[0])

            # Add to recent timing menu
            self.recent_timings.create(self.file)
            self._generate_recent_timing_menu()

        # Get all the data from the table + some magic
        data = self.central_list.get_items()

        # Then save it !
        AnimationTimer.write_timing_to_file(self.file.path(), data)

        self.data_changed = False
        self.change_window_title()

    def on_save_as_timing_triggered(self):
        """
        Save a timing into a file.
        Always ask for location before saving
        """
        # Just in case
        self.timer.stop()

        dialog = AnimationTimer._open_save_window(self)

        if dialog.exec_():
            filename = dialog.selectedFiles()
        else:
            return

        # Get all the data from the table + some magic
        data = self.central_list.get_items()

        # Then save it !
        AnimationTimer.write_timing_to_file(filename, data)

        # Set newly save filename as current file
        self.file = QtCore.QDir(filename[0])
        self.data_changed = False
        self.change_window_title()

        # Update to recent timing menu
        self.recent_timings.update(self.file)
        self._generate_recent_timing_menu()

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
        note = u""

        self.central_list.add(timer, frame, note)

    def on_recent_item_triggered(self):
        """
        Reload the file triggered.
        """
        filename = self.sender().text()

        self.load_timing(filename)

    # Files

    def load_timing(self, filename):
        """
            Actually load the file into the program.
        """
        data = AnimationTimer.read_timing_from_file(filename)
        # Couldn't laod the file.
        if data is None:
            # Delete the file if exists.
            try:
                self.recent_timings.delete(filename)
            except:
                pass

            # Set auto load to False, security.
            self.settings.setValue(
                "Preferences/auto_load_last_timing", False)
            self.preference_window.auto_load_timing.setChecked(False)

            # Regenerate the menu
            self._generate_recent_timing_menu()

            return False

        self.on_reset_btn_clicked()

        # Import the data
        self.import_data(data)

        # Set new file as the current file
        self.file = QtCore.QDir(filename)
        self.data = data
        self.data_changed = False
        self.change_window_title()
        self.current_timing_reload.setDisabled(True)

        # Add to recent timing menu
        self.recent_timings.create(self.file)
        self._generate_recent_timing_menu()

    # Others

    def import_data(self, data):
        fps = data[0].get('fps')

        for x in range(1, len(data)):
            time = data[x].get('time')
            frame = data[x].get('frame')
            note = data[x].get('note')
            self.central_list.add(time, frame, note)

        # Set fps
        self.fps_window.current = int(fps)
        self.fps.setText(str(fps) + " fps")

        self.central_list.horizontalHeader().show()

    def change_window_title(self):
        """
        Change the MainWindow title based on a loaded file and modifications.
        """
        # If no file (filename) so no starting data.
        if not self.file:
            if self.data_changed:
                self.setWindowTitle(TITLE + ': untitled *')
            else:
                self.setWindowTitle(TITLE + ': untitled')
        else:
            if self.data_changed:
                self.setWindowTitle(TITLE + ': ' + self.file.path() + ' *')
            else:
                self.setWindowTitle(TITLE + ': ' + self.file.path())

    def switch_filedialog_dir(self, path_only=True):
        """
        Get the default fir passed in the preferences window.
        ---
        2 choices:
        - Dir provided : Use it unless...
        - Dir provided : Use it unless...
        - Project dir enabled : if enabled, use it instead the default dir.
        """
        project_save_dir_enabled = _str_to_bool(self.settings.value(
            "Preferences/project_save_in_dirs", False))

        default_dir = QtCore.QDir(self.settings.value(
            "Preferences/default_directory"))

        # If no project enabled
        if not project_save_dir_enabled:
            directory = default_dir
        else:
            # If project enabled
            project_dir = cmds.workspace(q=True, rd=True)
            directory = QtCore.QDir(project_dir)

        if path_only:
            return directory.path()
        else:
            return directory

    def center_window(self):
        """
        Set the window at the center of the screen
        """
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _generate_recent_timing_menu(self):
        """
        Generate the menu list for the app menu.
        """
        if self.recent_timings.read():
            self.recent_timing_menu.clear()
            for value in self.recent_timings.read():
                recent_menu_item = QtGui.QAction(
                    value,
                    self)
                recent_menu_item.setAutoRepeat(False)
                recent_menu_item.triggered.connect(
                    self.on_recent_item_triggered)

                self.recent_timing_menu.addAction(recent_menu_item)
        else:
            self.recent_timing_menu.clear()
            self.recent_timing_menu.addAction(self.empty_action)

    @classmethod
    def load_settings_file(cls):
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

    # Overloading events
    # -------------------

    def closeEvent(self, event):
        # Save window attributes settings on close
        self._write_window_settings()

        # Save recent timing list
        self.recent_timings.save()

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
    Class for specific behavior operation.
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
    def calculate_time(cls, frame, fps, fmt="mm:ss:zzz"):
        """
        Calculte the time based on the frame and the current fps number
        :param frame: int
        :param fps: int
        :return:
        """

        ms = ceil(float(frame) / float(fps) * 1000)
        ms = int(ms)

        time = QtCore.QTime()
        m = time.addMSecs(ms).minute()
        sec = time.addMSecs(ms).second()
        msec = time.addMSecs(ms).msec()
        time.setHMS(0, m, sec, msec)

        return time.toString(fmt)

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
        d['fps'] = atui.fps_window.current

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
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except IOError:
            return error_display(
                "No file found : " + filename + ". "
                "The auto load for the last timing option was "
                "disabled.")

        name = data[0].get('plugin_name')
        fps = data[0].get('fps')

        if name == TITLE and fps:
            return data
        else:
            message = u'<p>Cannot load the file.</p>'
            message += u'Please verify it was meant to be used in this plugin.'

            QtGui.QMessageBox.information(
                atui,
                u'Cannot load the file.',
                message,
                QtGui.QMessageBox.Ok
            )
            return None

    @classmethod
    def _open_save_window(cls, parent):
        dialog = QtGui.QFileDialog(parent)
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('timing')
        dialog.setDirectory(atui.switch_filedialog_dir())
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
        auto_stop = atui.auto_stop_window.current

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
        auto_stop = atui.auto_stop_window.current

        if isinstance(auto_stop, int):
            if int(atui.frames.text()) >= auto_stop:
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
        if atui.auto_stop_window.current is not None:
            self.auto_stop_at_time()
            self.auto_stop_at_frame()

        # Set the default values.
        ms = self.elapsed()

        frames_amount = AnimationTimer.calculate_frames(
            ms,
            atui.fps_window.current)

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
        atui.timer_visual.setText(self.time.toString("mm:ss:zzz"))

        # Update the frames count.
        atui.frames.setNum(int(frames_amount))


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

        # Connections

        self.model.itemChanged.connect(self.on_data_changed)

    def add(self, time, frame, note):
        """
        Add a row to the table

        Item contents:
        - Time
        - Frame Number
        """
        self.set_headers()

        # Time
        row0 = QtGui.QStandardItem(str(time))
        row0.setEditable(False)
        row0.setTextAlignment(QtCore.Qt.AlignCenter)

        # Frame
        row1 = QtGui.QStandardItem(str(frame))
        row1.setEditable(True)
        row1.setTextAlignment(QtCore.Qt.AlignCenter)

        # Note
        row2 = QtGui.QStandardItem(str(note))
        row2.setEditable(True)
        row2.setToolTip(u"Double click to edit")
        row2.setTextAlignment(QtCore.Qt.AlignVCenter)

        l = [row0, row1, row2]

        self.model.appendRow(l)

    def remove(self):
        """
        Remove selected items.
        """
        i = self.selectionModel().selectedRows()
        for x in i:
            self.model.removeRow(x.row())

    def update_cell(self):
        pass

    def clear(self):
        """
        Clear the whole list.
        """
        self.model.clear()
        self.horizontalHeader().hide()

    def row_count(self):
        """
        Return the number of rows in the model
        ---
        Emits signals for specific case to help for other things.
        """
        return self.model.rowCount()

    def set_headers(self):
        """
        Set the headers for the list.
        """
        headers = list()
        headers.append(u"Times")
        headers.append(u"Frames")
        headers.append(u"Notes")

        self.model.setHorizontalHeaderLabels(headers)

    def get_items(self):
        """
        Create a dict of items ()
        """
        row_count = self.model.rowCount()

        l = []

        # For each line...
        for row in range(0, row_count):

            # Get data from the columns...
            d = dict()
            d["time"] = self.model.item(row, 0).text()
            d["frame"] = self.model.item(row, 1).text()
            d["note"] = self.model.item(row, 2).text()

            l.append(d)

        return l

    # EVENTS
    # ------

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            atui.on_start_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            atui.on_stop_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Backspace:
            if len(self.selectionModel().selectedRows()) > 0:
                self.remove()
            else:
                atui.on_reset_btn_clicked()

            event.accept()
        else:
            # make sure usual keys get dealt with
            super(CenterList, self).keyPressEvent(event)

    # SIGNALS
    # -------

    def on_data_changed(self, item):
        """
        Catch a signal when an item is changed in the table.
        ---
        - When a note is changed, do nothing.
        - When a frame number is changed, verify it is a number, then :
            - if less than the previous number in the column, make it +1
            - if more than the next number in the column, make in - 1
            - Then calculate the nuw time based on the frame number and fps number.
            - Update the data !
        """
        current_row = item.row()
        current_column = item.column()
        text = item.text()

        # If the modified item is not in the column 1 (frames), stop there.
        if current_column != 1:
            return

        # Verify user enters only numbers
        try:
            text = int(text)
        except ValueError:
            return warning_display("Animation Timer : Frame can only be valid number.")

        # Get the previous and next items
        previous_item = self.model.item(current_row - 1, current_column)
        next_item = self.model.item(current_row + 1, current_column)

        if previous_item is not None:
            previous_text = int(previous_item.text())

            if text <= previous_text:
                item.setText(str(text + 1))

        if next_item is not None:
            next_text = int(next_item.text())

            if text >= next_text:
                item.setText(str(text - 1))

        time_formated = AnimationTimer.calculate_time(text, atui.fps_window.current)
        time_item = self.model.item(current_row, 0)
        time_item.setText(time_formated)


class FramePerSecondWindow(QtGui.QDialog):

    fps_preset_list = [6, 12, 15, 24, 25, 30, 48, 50, 60]
    default = 24
    min_fps = 6
    max_fps = 120

    def __init__(self, parent=None):
        super(FramePerSecondWindow, self).__init__(parent)

        self.current = None

        self.setWindowTitle(u"Choose FPS")
        self.setFixedSize(250, 150)

        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.settings = AnimationTimerUI.load_settings_file()
        self.settings.setFallbacksEnabled(False)
        self._read_pref_settings()

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
        self.fps_custom_spinbox.setRange(
            FramePerSecondWindow.min_fps, FramePerSecondWindow.max_fps)
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

        self.current = FramePerSecondWindow.default

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

        atui.fps.setText(str(self.current) + " fps")
        return self.accept()

    def on_rejected(self):
        return self.reject()

    # Settings

    def _read_pref_settings(self):
        self.settings.beginGroup("Preferences")

        default_fps = self.settings.value("default_fps", 24)
        FramePerSecondWindow.default = int(default_fps)

        self.settings.endGroup()


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
            atui.timing_option_btn.setText("No Auto Stop")

        if self.radio_time.isChecked():
            self.current = self.time_edit.time()
            atui.timing_option_btn.setText(
                "Auto Stop at " + self.time_edit.time().toString("mm:ss:zzz"))

        if self.radio_frames.isChecked():
            self.current = int(self.frames_spinbox.value())
            frame_text = ' frame' if str(self.current) == '1' else ' frames'
            atui.timing_option_btn.setText(
                "Auto Stop at " + str(self.current) + frame_text)

        return self.accept()

    def on_rejected(self):
        return self.reject()


class RecentTiming(object):

    max_timing = 10

    def __init__(self, parent):
        self.parent = parent
        self.recent_list = []

        self.settings = AnimationTimerUI.load_settings_file()
        self.settings.setFallbacksEnabled(False)

        self.max_count = int(self.settings.value(
            "max_recent_timing", RecentTiming.max_timing))

        self._load_from_file()

    def create(self, filename):
        """
        Add a recent timing to the list.
        ---
        - filename : QDir object with filename.
        """
        if isinstance(filename, QtCore.QDir):

            # If item already exists
            if self.recent_list.count(filename.path()):
                self.update(filename)
            # Else...
            else:
                if self.count() >= self.max_count:
                    self.recent_list.pop()

                self.recent_list.insert(0, filename.path())

        self._uniqify()

    def read(self, index=-1):
        """
        Read recent timings filename or just one if index exists.
        ---
        - index : [n] index. 0 is the minimum. -1 is None like.
        """
        if index < 0:
            return self.recent_list
        else:
            return self.recent_list[index]

    def update(self, filename, index=0):
        """
        Update a recent timing in the list.
        ---
        - filename : QDir object with filename.
        - index : new index to move it to [default: 0]
        """
        if isinstance(filename, QtCore.QDir):
            try:
                self.recent_list.remove(filename.path())
                self.recent_list.insert(index, filename.path())
            except ValueError:
                pass

            self._uniqify()

    def delete(self, data):
        """
        Remove a recent timing from the list.
        ---
        - data : QDir object with filename or list index.
        """
        if isinstance(data, QtCore.QDir):
            self.recent_list.remove(data.path())
        elif isinstance(data, basestring):
            self.recent_list.remove(data)
        elif isinstance(data, int):
            self.recent_list.pop(data)
        else:
            return False

        self._uniqify()

    def clear(self):
        """
        Clear the whole list.
        """
        self.recent_list = []
        return self.recent_list

    def reload(self):
        """
        Reload the recent timing list.
        """
        self.clear()
        self._load_from_file()

    def count(self):
        return len(self.recent_list)

    def save(self):
        """
        Launch the save process.
        """
        return self._save_to_file()

    def load(self):
        """
        Launch the load process.
        """
        return self._load_from_file()

    # ---

    def _uniqify(self):
        """
        Make sure all link in the list are unique !
        """
        known_list = set()
        newlist = []

        for item in self.recent_list:
            if item in known_list:
                continue
            newlist.append(item)
            known_list.add(item)

        self.recent_list[:] = newlist

    def _save_to_file(self):
        """
        Save new stuff to animation timer settings ini file.
        """
        self.settings.beginGroup("RecentTimings")
        self.settings.remove('')  # Remove all key into that group

        self._uniqify()  # Make sure every line is unique

        for key, value in enumerate(self.recent_list):
            self.settings.setValue(
                "recent_" + str(key + 1),
                value)

        self.settings.endGroup()

    def _load_from_file(self):
        """
        Load data from the animation timing settings ini file.
        """
        self.settings.beginGroup("RecentTimings")

        keys = self.settings.allKeys()

        if keys:
            for key in keys:
                self.recent_list.append(
                    self.settings.value(key))

        self._uniqify()

        self.settings.endGroup()


class AnimationTimerPreferences(QtGui.QDialog):

    def __init__(self, parent):
        super(AnimationTimerPreferences, self).__init__(parent)

        self.setWindowTitle(u'Preferences')
        self.setFixedSize(400, 350)

        self.create_layout()
        self.create_connections()

        self.settings = AnimationTimerUI.load_settings_file()
        self.settings.setFallbacksEnabled(False)
        self._read_pref_settings()

    def create_layout(self):

        policy = QtGui.QSizePolicy()
        policy.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        policy.setVerticalPolicy(QtGui.QSizePolicy.Fixed)

        # Set Widgets

        # Menu List
        self.menu_list = QtGui.QListWidget()
        self.menu_list.setFixedWidth(100)
        self.menu_list.addItem(u'General')
        self.menu_list.addItem(u'Project')
        self.menu_list.addItem(u'Recent Timings')
        self.menu_list.setCurrentRow(0)
        self.menu_list.setStyleSheet("background-color:#191919;")

        # Set Default FPS
        self.default_custom_fps_spinbox = QtGui.QSpinBox()
        self.default_custom_fps_spinbox.setRange(
            FramePerSecondWindow.min_fps, FramePerSecondWindow.max_fps)
        self.default_custom_fps_spinbox.setSingleStep(2)

        self.default_fps_label = QtGui.QLabel(u"fps")

        self.default_fps_layout = QtGui.QGridLayout()
        self.default_fps_layout.addWidget(
            self.default_custom_fps_spinbox, 0, 0)
        self.default_fps_layout.addWidget(self.default_fps_label, 0, 1)
        self.default_fps_layout.setColumnStretch(0, 1)

        self.default_fps_group = QtGui.QGroupBox(u"Default FPS")
        self.default_fps_group.setLayout(self.default_fps_layout)
        self.default_fps_group.setSizePolicy(policy)

        # Set Save Default Directory
        self.default_dir_lineedit = QtGui.QLineEdit()
        self.default_dir_lineedit.setReadOnly(True)
        self.default_dir_btn = QtGui.QPushButton(u'...')
        self.default_dir_btn.setFixedWidth(30)
        self.default_dir_desc = QtGui.QLabel(
            u'Will be used if you choose not to save timings in '
            'projects directories.<br>"Save as..." action will always let '
            'you choose where to save.')
        self.default_dir_desc.setWordWrap(True)
        self.default_dir_desc.setStyleSheet("""
                                            color:#888888;
                                            font-style:italic;
                                            """)

        self.default_dir_hbox = QtGui.QHBoxLayout()
        self.default_dir_hbox.addWidget(self.default_dir_lineedit)
        self.default_dir_hbox.addWidget(self.default_dir_btn)

        self.default_dir_vbox = QtGui.QVBoxLayout()
        self.default_dir_vbox.addLayout(self.default_dir_hbox)
        self.default_dir_vbox.addWidget(self.default_dir_desc)

        self.default_dir_group = QtGui.QGroupBox(u'Default save directory')
        self.default_dir_group.setLayout(self.default_dir_vbox)

        # Auto load the last timing opened
        self.auto_load_timing = QtGui.QCheckBox(
            u"Auto load last timing you worked on.")

        self.auto_load_timing_vbox = QtGui.QVBoxLayout()
        self.auto_load_timing_vbox.addWidget(self.auto_load_timing)

        self.auto_load_timing_group = QtGui.QGroupBox(
            u'When application starts')
        self.auto_load_timing_group.setLayout(self.auto_load_timing_vbox)

        # Projects

        # Save timings in project directories
        self.project_save_in_dirs = QtGui.QCheckBox(
            u"Save timings in projects directories")

        # Recent Timings

        # Number to remember
        self.recent_timing_label = QtGui.QLabel(u'timings')
        self.recent_timing_spinbox = QtGui.QSpinBox()
        self.recent_timing_spinbox.setFixedWidth(40)
        self.recent_timing_spinbox.setValue(10)
        self.recent_timing_spinbox.setRange(0, 20)
        self.recent_timing_spinbox.setButtonSymbols(
            QtGui.QAbstractSpinBox.NoButtons)
        self.recent_timing_spinbox.setSingleStep(1)

        self.recent_timing_hbox = QtGui.QHBoxLayout()
        self.recent_timing_hbox.addWidget(self.recent_timing_spinbox)
        self.recent_timing_hbox.addWidget(self.recent_timing_label)

        self.recent_timing_group = QtGui.QGroupBox(
            u'Number to remember')
        self.recent_timing_group.setLayout(self.recent_timing_hbox)

        #  Button Box
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                                 QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)

        # Set Pages

        # General tab
        self.vbox_general = QtGui.QVBoxLayout()
        self.vbox_general.setAlignment(QtCore.Qt.AlignTop)
        self.vbox_general.addWidget(self.default_fps_group)
        self.vbox_general.addWidget(self.default_dir_group)
        self.vbox_general.addWidget(self.auto_load_timing_group)

        self.tab_general = QtGui.QWidget()
        self.tab_general.setLayout(self.vbox_general)

        # Project tab
        self.vbox_project = QtGui.QVBoxLayout()
        self.vbox_project.setAlignment(QtCore.Qt.AlignTop)
        self.vbox_project.addWidget(self.project_save_in_dirs)

        self.tab_project = QtGui.QWidget()
        self.tab_project.setLayout(self.vbox_project)

        # Recent Timings tab
        self.vbox_recent_timings = QtGui.QVBoxLayout()
        self.vbox_recent_timings.setAlignment(QtCore.Qt.AlignTop)
        self.vbox_recent_timings.addWidget(self.recent_timing_group)

        self.tab_recent_timings = QtGui.QWidget()
        self.tab_recent_timings.setLayout(self.vbox_recent_timings)

        # Stacked the *pages*
        self.menu_stacked = QtGui.QStackedWidget()
        self.menu_stacked.addWidget(self.tab_general)
        self.menu_stacked.addWidget(self.tab_project)
        self.menu_stacked.addWidget(self.tab_recent_timings)

        # Layout for widgets
        self.main_hbox = QtGui.QHBoxLayout()
        self.main_hbox.addWidget(self.menu_list)
        self.main_hbox.addWidget(self.menu_stacked)

        # layout for main + buttons
        self.main_vbox = QtGui.QVBoxLayout()
        self.main_vbox.addLayout(self.main_hbox)
        self.main_vbox.addWidget(self.button_box)

        self.setLayout(self.main_vbox)

    def create_connections(self):
        self.menu_list.currentItemChanged.connect(self._change_current_tab)

        self.default_dir_btn.clicked.connect(self._select_dir)

    def on_accepted(self):
        self._write_pref_settings()
        return self.accept()

    def on_rejected(self):
        return self.reject()

    # SLOTS
    # -----

    def _change_current_tab(self):
        row = self.menu_list.currentRow()
        self.menu_stacked.setCurrentIndex(row)

    def _select_dir(self):

        directory = QtGui.QFileDialog.getExistingDirectory(
            self,
            u"Select a default directory",
            '',
            QtGui.QFileDialog.DontUseNativeDialog |
            QtGui.QFileDialog.ShowDirsOnly
            )

        if directory:
            self.default_dir_lineedit.setText(directory)
        else:
            return

    # Settings
    # --------

    def _read_pref_settings(self):
        self.settings.beginGroup("Preferences")

        # General
        self.default_custom_fps_spinbox.setValue(
            int(self.settings.value("default_fps", 24)))

        # Dir...
        directory = QtCore.QDir(
            self.settings.value(
                "default_directory",
                QtCore.QDir.homePath()))
        self.default_dir_lineedit.setText(directory.path())

        self.recent_timing_spinbox.setValue(
            int(self.settings.value("max_recent_timing", 10)))

        self.auto_load_timing.setChecked(
            _str_to_bool(self.settings.value("auto_load_last_timing", False)))

        # Project
        self.project_save_in_dirs.setChecked(
            _str_to_bool(self.settings.value("project_save_in_dirs", True)))

        self.settings.endGroup()

    def _write_pref_settings(self):
        """
        Write settings into the config file
        """
        self.settings.beginGroup("Preferences")

        # General
        self.settings.setValue(
            "default_fps",
            self.default_custom_fps_spinbox.value())

        # For directory, passes it to QDir for multi-system
        directory = QtCore.QDir(self.default_dir_lineedit.text())
        self.settings.setValue(
            "default_directory",
            directory.path())

        self.settings.setValue(
            "max_recent_timing",
            self.recent_timing_spinbox.value())

        self.settings.setValue(
            "auto_load_last_timing",
            self.auto_load_timing.isChecked())

        # Project
        self.settings.setValue(
            "project_save_in_dirs",
            self.project_save_in_dirs.isChecked())

        self.settings.endGroup()


def show():
    """
    Simply launching the program.
    """
    global atui

    try:
        atui.close()
    except:
        pass

    atui = AnimationTimerUI()
    atui.show()


# Possibility to run the program by launching it simply...
if __name__ == "__main__":

    try:
        atui.close()
    except:
        pass

    atui = AnimationTimerUI()
    atui.show()