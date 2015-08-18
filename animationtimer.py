# -*- coding: utf-8 -*-

"""
Animation Timer.
---

Get timings out of your head !

This script aims to help animators get rough timings they have inside their head
into usable information like times and frames to speed up the blocking process.

---

Copyright 2015 Yann Schmidt

Animation Timer is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

Animation Timer is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Animation Timer.
If not, see http://www.gnu.org/licenses/.

All advertising materials mentioning features or use of this software must display the following acknowledgement:
- Direct mention of the author.
- A link to the main page of the plugin in the official's author website.
"""

__author__ = u"Yann Schmidt"
__version__ = u"1.4.1"
__license__ = u"GPL"
__email__ = u"contact@yannschmidt.com"
__maya__ = u"2014+"

from PySide import QtCore, QtGui
from shiboken import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import pymel.core as pm

import os
import json
from math import ceil
from datetime import datetime


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
    MAXIMUM_HEIGHT = 700

    def __init__(self, parent=maya_main_window()):
        super(AnimationTimerUI, self).__init__(parent)

        self.setWindowTitle(AnimationTimer.TITLE)
        self.setMinimumSize(AnimationTimerUI.MINIMUM_WIDTH, AnimationTimerUI.MINIMUM_HEIGHT)
        self.setMaximumSize(AnimationTimerUI.MAXIMUM_WIDTH, AnimationTimerUI.MAXIMUM_HEIGHT)
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

        # Windows attached
        self.preference_window = AnimationTimerPreferences(self)
        self.options_window = AnimationTimerOptions(self)

        # Node
        self.node = ATNode(self)

        # Auto-Populate window
        self.populate()

        # File management
        self.file = None
        self.recent_timings = ATRecentTimings(self)

        self.setStyleSheet("""
                           QPushButton:pressed {
                               background-color: #606060;
                               border: transparent;
                           }
                           QPushButton:checked {
                               background-color: transparent;
                               border: 1px solid green;
                           }
                           """)

    # ---

    def create_actions(self):
        """
        Create actions mainly for the main menu.
        """
        # Action : New Timing
        self.action_new_timing = QtGui.QAction(u"New Timing", self)
        self.action_new_timing.setStatusTip(u"Create a new Timing")
        self.action_new_timing.setAutoRepeat(False)

        # Action : Open Timing
        self.action_open_timing = QtGui.QAction(u"Open Timing", self)
        self.action_open_timing.setStatusTip(u"Open existing Timing (.timing | .json)")
        self.action_open_timing.setAutoRepeat(False)

        # Action : Recent Timing (empty at first)
        self.submenu_recent_timing = QtGui.QMenu(u'Recent Timings', self)

        self.submenu_empty_action = QtGui.QAction(u'Empty', self)
        self.submenu_empty_action.setDisabled(True)

        # Action : Save
        self.action_save_timing = QtGui.QAction(u"Save", self)
        self.action_save_timing.setStatusTip(u"Save Timing")
        self.action_save_timing.setAutoRepeat(False)

        # Action : Save As...
        self.action_save_timing_as = QtGui.QAction(u"Save As ...", self)
        self.action_save_timing_as.setStatusTip(u"Save Timing as ...")
        self.action_save_timing_as.setAutoRepeat(False)

        # Action : Exit Program
        self.action_exit_app = QtGui.QAction(u"Exit", self)
        self.action_exit_app.setStatusTip(u"Close this script")

        # ---

        # Action : Discard current changes
        self.action_discard_current_changes = QtGui.QAction(u"Discard changes", self)
        self.action_discard_current_changes.setStatusTip(u"Discard all changes made since you opened/created this timing.")
        self.action_discard_current_changes.setAutoRepeat(False)

        # Action : Reset Offsets
        self.action_reset_offsets = QtGui.QAction(u"Reset Offsets", self)
        self.action_reset_offsets.setStatusTip(u"Reset offsets both from time and frames.")
        self.action_reset_offsets.setAutoRepeat(False)

        # Action : Open Preference Window
        self.action_preferences_window = QtGui.QAction(u"Preferences", self)
        self.action_preferences_window.setStatusTip(u"Open the preferences window")

        # ---

        # Action : Show on Maya TimeLine
        self.action_timing_on_timeline = QtGui.QAction(u"Show on Timeline", self)
        self.action_timing_on_timeline.setStatusTip(u"Show on Maya Timeline")
        self.action_timing_on_timeline.setCheckable(True)

        # ---

        # Action : Reset Window Size
        self.action_reset_window_size = QtGui.QAction(u"Reset window size", self)
        self.action_reset_window_size.setAutoRepeat(False)
        self.action_reset_window_size.setStatusTip(u"Reset the window to its original size")

        # Action : Show / Hide Interval Column
        self.action_column_interval = QtGui.QAction(u"Show Interval Column", self)
        self.action_column_interval.setStatusTip(u"Toggle the visibility of the Interval column")
        self.action_column_interval.setCheckable(True)

        # Action : Show / Hide Note Column
        self.action_column_note = QtGui.QAction(u"Show Note Column", self)
        self.action_column_note.setStatusTip(u"Toggle the visibility of the Note column")
        self.action_column_note.setCheckable(True)

        # Action : Always on Top
        self.action_always_on_top = QtGui.QAction(u"Always on Top", self)
        self.action_always_on_top.setCheckable(True)
        self.action_always_on_top.setStatusTip(u"Toggle the window to always on top of the screen")

        # ---

        # Action : Documentations
        self.action_open_docs = QtGui.QAction(u"Documentation", self)
        self.action_open_docs.setStatusTip(u"Open the Documentation inside a web browser")

        # Action : Add to Shelf
        self.action_add_to_shelf = QtGui.QAction(u"Add to Shelf", self)
        self.action_add_to_shelf.setStatusTip(u"Add a shortcut to the selected shelf.")

        # Action : About Window
        self.action_about_window = QtGui.QAction(u"About", self)
        self.action_about_window.setStatusTip(u"About Animation Timer")
        self.action_about_window.setAutoRepeat(False)

    def create_menu(self):
        """
        Create the main menu and associates actions to it.
        """
        menubar = self.menuBar()

        # File menu
        self.menubar_file = menubar.addMenu(u"File")
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
        self.menubar_edit = menubar.addMenu(u"Edit")
        self.menubar_edit.setTearOffEnabled(True)
        self.menubar_edit.addAction(self.action_discard_current_changes)
        self.menubar_edit.addAction(self.action_reset_offsets)
        self.menubar_edit.addSeparator()
        self.menubar_edit.addAction(self.action_preferences_window)

        # Maya menu
        self.menubar_maya = menubar.addMenu(u"Maya")
        self.menubar_maya.addAction(self.action_timing_on_timeline)

        # Window menu
        self.menubar_window = menubar.addMenu(u"Window")
        self.menubar_window.addAction(self.action_reset_window_size)
        self.menubar_window.addSeparator()
        self.menubar_window.addAction(self.action_column_interval)
        self.menubar_window.addAction(self.action_column_note)
        self.menubar_window.addSeparator()
        self.menubar_window.addAction(self.action_always_on_top)

        # Help menu
        self.menubar_help = menubar.addMenu(u"Help")
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
        self.file_info_label = QtGui.QLabel(u"Untitled")
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
        self.start_btn.setStyleSheet("""
                                     font-size:20px;
                                     """)

        self.vline = QtGui.QFrame()
        self.vline.setFrameShape(QtGui.QFrame.VLine)

        self.stop_btn = QtGui.QPushButton(u"Stop")
        self.stop_btn.setStyleSheet("""
                                    font-size:20px;
                                    """)
        self.stop_btn.setFlat(True)

        self.reset_btn = QtGui.QPushButton()
        self.reset_btn.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'at_reset.png')).path()).pixmap(16, 16))
        self.reset_btn.setIconSize(QtCore.QSize(32, 32))
        self.reset_btn.setFixedSize(32, 32)
        self.reset_btn.setToolTip(u"Reset")
        self.reset_btn.setFlat(True)

        self.options_btn = QtGui.QPushButton()
        self.options_btn.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'at_options.png')).path()).pixmap(16, 16))
        self.options_btn.setIconSize(QtCore.QSize(32, 32))
        self.options_btn.setFixedSize(32, 32)
        self.options_btn.setToolTip(u"Options Panel")
        self.options_btn.setFlat(True)

        self.sound_btn = QtGui.QPushButton()
        self.sound_btn.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'at_sound.png')).path()).pixmap(16, 16))
        self.sound_btn.setIconSize(QtCore.QSize(32, 32))
        self.sound_btn.setFixedSize(32, 32)
        self.sound_btn.setToolTip(u"Toggle Sound Playback")
        self.sound_btn.setFlat(True)
        self.sound_btn.setCheckable(True)
        # self.sound_btn.setAccessibleName('SoundButton')

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
        self.action_new_timing.triggered.connect(self.on_new_file_action_triggered)
        self.action_open_timing.triggered.connect(self.on_open_file_action_triggered)
        self.action_save_timing.triggered.connect(self.on_save_timing_action_triggered)
        self.action_save_timing_as.triggered.connect(self.on_save_timing_as_action_triggered)
        self.action_exit_app.triggered.connect(self.on_exit_app_action_triggered)
        self.action_discard_current_changes.triggered.connect(self.on_discard_changes_triggered)
        self.action_reset_offsets.triggered.connect(self.on_reset_offsets_triggered)
        self.action_preferences_window.triggered.connect(self.open_preference_window)
        self.action_timing_on_timeline.triggered.connect(self.on_show_on_timeline_triggered)
        self.action_reset_window_size.triggered.connect(self.on_action_reset_window_size_triggered)
        self.action_column_interval.triggered.connect(self.central_list.col_interval_toggle_visibility)
        self.action_column_note.triggered.connect(self.central_list.col_note_toggle_visibility)
        self.action_always_on_top.triggered.connect(self.on_window_always_on_top_triggered)
        self.action_open_docs.triggered.connect(AnimationTimer.on_open_docs_triggered)
        self.action_add_to_shelf.triggered.connect(AnimationTimer.on_add_to_shelf)
        self.action_about_window.triggered.connect(self.open_about_window)

        self.start_btn.clicked.connect(self.on_start_btn_clicked)
        self.stop_btn.clicked.connect(self.on_stop_btn_clicked)
        self.reset_btn.clicked.connect(self.on_reset_btn_clicked)
        self.options_btn.clicked.connect(self.on_options_btn_clicked)

    # ---

    def populate(self):
        """
        Populate the interface at first start.
        :return:
        """
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.action_reset_offsets.setEnabled(False)
        self.action_discard_current_changes.setEnabled(False)

        self.on_window_always_on_top_triggered()

        if self.node.exists():
            self.action_timing_on_timeline.setChecked(True)

    def open_about_window(self):
        message = u'<h3>%s</h3>' % AnimationTimer.TITLE
        message += u'<p>Version: {0}<br>'.format(AnimationTimer.VERSION)
        message += u'Maya: {0}<br>'.format(__maya__)
        message += u'Author:  %s</p>' % AnimationTimer.AUTHOR
        message += u'<a style="color:white;" \
        href="http://www.yannschmidt.com">http://www.yannschmidt.com</a><br><br>'
        message += u'<a style="color:white;" \
        href="https://twitter.com/yannschmidt">Updates on Twitter</a>'
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
            self._capture()
        else:
            self.central_list.clear()
            self.timer.start()
            self.start_btn.setText("Capture")

        self.stop_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)

    def on_stop_btn_clicked(self):
        self.timer.stop()
        self.start_btn.setText(u"Start")
        self.stop_btn.setDisabled(True)

    def on_reset_btn_clicked(self):
        if self.timer.isActive():
            self.timer.stop()

        self._reset_timer()
        self._reset_frame_counter()

        # Empty the table
        self.central_list.clear()

        self.start_btn.setText(u"Start")
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)

    def on_options_btn_clicked(self):

        fps = self.fps_label.text()
        if int(fps) in AnimationTimerOptions.fps_preset_list:
            self.options_window.on_fps_preset_selected()
            i = self.options_window.fps_combobox.findText(str(fps))
            self.options_window.fps_combobox.setCurrentIndex(i)
        else:
            self.options_window.on_fps_custom_selected()
            self.options_window.fps_custom_spinbox.setValue(int(fps))

        if self.options_window.isVisible():
            self.options_window.hide()
        else:
            self.options_window.show()

    # Other Actions

    def on_new_file_action_triggered(self):
        """
        Perform actions when 'new file" action is selected.
        A new file reset the offset and the fps number.
        :return: void
        """
        # Reset interface
        self.on_reset_btn_clicked()
        self.on_reset_offsets_triggered()
        self.fps_label.setNum(int(AnimationTimerOptions.default_fps))
        self.file_info_label.setText(u"Untitled")

        # Set new file
        self.file = None

    def on_open_file_action_triggered(self):
        """
        Open a saved file.
        :return: void
        """
        # Security
        self.on_stop_btn_clicked()

        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self,
            'Open Timing',
            AnimationTimer.switch_filedialog_dir(),
            'Timing / Json FIles (*.timing *.json)',
            '',
            QtGui.QFileDialog.DontUseNativeDialog
        )

        if not filename:
            return

        self.file = ATFile(filename, self)
        self.file.load()

    def on_save_timing_action_triggered(self):
        """
        Save a timing into a file.
        If file exists, do not ask location.
        :return: void
        """
        # Security
        self.on_stop_btn_clicked()

        if not self.file:
            if not self.central_list.changed:
                return AnimationTimer.warning(u"Animation Timer: Why save an empty file ?")

            dialog = AnimationTimer.open_save_window(self)

            if dialog.exec_():
                file_list = dialog.selectedFiles()
            else:
                return AnimationTimer.warning(u"Animation Timer: Canceled saving file.")

            self.file = ATFile(file_list[0], self)
            self.file.save()
        else:
            self.file.save()

    def on_save_timing_as_action_triggered(self):
        """
        Save a timing into a file.
        Always ask for location.
        :return: void
        """
        # Security
        self.on_stop_btn_clicked()

        if not self.file and not self.central_list.changed:
            return AnimationTimer.warning(u"Animation Timer: Why save an empty file ?")

        dialog = AnimationTimer.open_save_window(self)

        if dialog.exec_():
            file_list = dialog.selectedFiles()
        else:
            return AnimationTimer.warning(u"Animation Timer: Canceled saving file.")

        self.file = ATFile(file_list[0], self)
        self.file.save()

    def on_exit_app_action_triggered(self):

        if self.central_list.changed:
            message = u'The timing your are working on has changed.'
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

    def on_discard_changes_triggered(self):
        if self.central_list.changed:
            if self.file is None:
                self.on_new_file_action_triggered()
            else:
                pass  # TODO: If file, reload it.

    def on_reset_offsets_triggered(self):
        # Clear offsets in option window then accept.
        self.options_window.on_clear_offset_time_clicked()
        self.options_window.on_clear_offset_frame_clicked()
        self.options_window.on_accepted()

        self._reset_timer()
        self._reset_frame_counter()

        self.action_reset_offsets.setEnabled(False)

    def on_show_on_timeline_triggered(self):
        """
        Create a Node specially for this purpose.
        :return: void
        """
        if self.action_timing_on_timeline.isChecked():
            self.node.create()
        else:
            self.node.delete()

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

    def on_recent_item_triggered(self):
        filename = self.sender().text()

        self.file = ATFile(filename, self)
        self.file.load()

    # --

    def _reset_timer(self):
        if self.timer.offset:
            self.timer.time = QtCore.QTime(0, 0, 0).addMSecs(self.timer.offset)
            self.timer_label.setText(self.timer.time.toString("mm:ss:zzz"))
        else:
            self.timer_label.setText("00:00:000")
            self.timer.time = QtCore.QTime()

    def _reset_frame_counter(self):
        if self.timer.offset:
            self.frame_counter_label.setNum(AnimationTimer.calculate_frames(self.timer.offset, int(self.fps_label.text())))
        else:
            self.frame_counter_label.setNum(0)

    def _capture(self):
        """
        Capture current time, frame count and notes and an instant 't'.
        :return: void
        """
        time = self.timer.time.toString("mm:ss:zzz")
        frame = self.frame_counter_label.text()
        note = u''

        self.central_list.add_row(time, frame, note)

        if self.action_timing_on_timeline.isChecked():
            self.node.add(frame)

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

        self.action_always_on_top.setChecked(bool_str(settings.value("always_on_top", True)))

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
    AUTHOR = __author__
    VERSION = __version__
    USER_SCRIPT_DIR = pm.system.internalVar(userScriptDir=True)
    USER_PREFS_DIR = pm.system.internalVar(userPrefDir=True)
    ICON_DIR = os.path.join(pm.system.internalVar(userPrefDir=True), 'icons')
    DOCS_URL = "http://www.yannschmidt.com/docs/product/scripts/animation-timer/"

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

    # ---

    @classmethod
    def on_add_to_shelf(cls):
        """
        Add a program shortcut into a shelf.
        :return void
        """
        # Query the current selected shelf.
        g_shelf_top_level = pm.language.mel.eval('$temp1=$gShelfTopLevel')
        current_shelf = pm.shelfTabLayout(g_shelf_top_level, q=True, st=True)

        return pm.windows.shelfButton(
            p=current_shelf,
            rpt=True,
            image="pythonFamily.png",
            image1="at_shelficon.png",
            stp="python",
            iol="AT",
            annotation=u"Open Animation Timer v%s" % AnimationTimer.VERSION,
            label=u"Open Animation Timer v%s" % AnimationTimer.VERSION,
            command="import animationtimer; animationtimer.show()"
        )

    @classmethod
    def on_open_docs_triggered(cls):
        url = QtCore.QUrl(AnimationTimer.DOCS_URL)
        return QtGui.QDesktopServices.openUrl(url)

    @classmethod
    def open_save_window(cls, parent):
        dialog = QtGui.QFileDialog(parent)
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('timing')
        dialog.setDirectory(AnimationTimer.switch_filedialog_dir())
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setNameFilter(
            'Timing File (*.timing);;Json File (*.json)')
        dialog.setWindowTitle("Save Timing as ...")
        dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog)

        return dialog

    @classmethod
    def switch_filedialog_dir(cls, path_only=True):
        """
        Get the default fir passed in the preferences window.
        ---
        2 choices:
        - Dir provided : Use it unless...
        - Project dir enabled : if enabled, use it instead the default dir.
        """
        settings = AnimationTimer.load_settings_file()
        project_save_dir_enabled = bool_str(settings.value(
            "Preferences/project_save_in_dirs", False))

        default_dir = QtCore.QDir(settings.value(
            "Preferences/default_directory"))

        # If no project enabled
        if not project_save_dir_enabled:
            directory = default_dir
        else:
            # If project enabled
            project_dir = pm.workspace.getPath()
            directory = QtCore.QDir(project_dir)

        if path_only:
            return directory.path()
        else:
            return directory

    # ---

    @classmethod
    def info(cls, msg):
        return om.MGlobal.displayInfo(msg)

    @classmethod
    def warning(cls, msg):
        return om.MGlobal.displayWarning(msg)

    @classmethod
    def error(cls, msg):
        return om.MGlobal.displayError(msg)


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
        self.parent = parent

        self.time = QtCore.QTime()
        self.offset = 0  # ms

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
        frames = AnimationTimer.calculate_frames(int(ms), int(self.parent.fps_label.text()))

        # Update displays
        self.parent.timer_label.setText(self.time.toString("mm:ss:zzz"))
        self.parent.frame_counter_label.setNum(int(frames))


class ATCenterList(QtGui.QTableWidget):
    """
    Center List object.
    """

    COLS_NAMES = ['Time', 'Frame', 'Interval', 'Note']
    MAX_COLS = 4

    rowAdded = QtCore.Signal()
    rowsCleared = QtCore.Signal()
    contentChanged = QtCore.Signal(bool)

    def __init__(self, parent):
        super(ATCenterList, self).__init__(parent)
        self.parent = parent

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setGridStyle(QtCore.Qt.DashLine)

        self.changed = False

        # Handle Shortcuts
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Connexions
        self.rowAdded.connect(self.on_content_changed)
        self.rowsCleared.connect(self.on_content_changed)
        self.verticalHeader().sectionClicked.connect(self.on_vertical_header_clicked)

    def add_row(self, time, frame, note):
        """
        Append a new row to the table.
        """
        # If nothing yet... Initialize !
        if not self.rowCount():
            self._init()

        # Create a new empty row
        self.insertRow(self.rowCount())

        # Create cells
        time_cell = QtGui.QTableWidgetItem(str(time))
        time_cell.setFlags(time_cell.flags() ^ QtCore.Qt.ItemIsEditable)
        time_cell.setTextAlignment(QtCore.Qt.AlignCenter)

        frame_cell = QtGui.QTableWidgetItem(str(frame))
        frame_cell.setFlags(frame_cell.flags() ^ QtCore.Qt.ItemIsEditable)
        frame_cell.setTextAlignment(QtCore.Qt.AlignCenter)

        interval_cell = QtGui.QTableWidgetItem(u'-')
        interval_cell.setFlags(interval_cell.flags() ^ QtCore.Qt.ItemIsEditable)
        interval_cell.setTextAlignment(QtCore.Qt.AlignCenter)

        # Calc interval
        if self.rowCount() > 1:
            interval = int(frame) - int(self.item(self.rowCount() - 2, 1).text())
            interval_cell.setText(str(interval))

        note_cell = QtGui.QTableWidgetItem(str(note))
        note_cell.setToolTip(u"Double click to edit")
        note_cell.setTextAlignment(QtCore.Qt.AlignVCenter)

        # Set items
        self.setItem(self.rowCount() - 1, 0, time_cell)
        self.setItem(self.rowCount() - 1, 1, frame_cell)
        self.setItem(self.rowCount() - 1, 2, interval_cell)
        self.setItem(self.rowCount() - 1, 3, note_cell)

        # Emit a signal
        self.rowAdded.emit()

    def export_data(self):
        """
        Export all data in the table as a dict.
        Can be used for saving data in a file.
        :return: dict
        """
        l = list()

        for row in range(0, self.rowCount()):

            temp = dict()
            temp['time'] = self.item(row, 0).text()
            temp['frame'] = self.item(row, 1).text()
            temp['interval'] = self.item(row, 2).text()
            temp['note'] = self.item(row, 3).text()

            l.append(temp)

        return l

    def import_data(self, data):
        """
        Import data to the central widget list.
        :param data: list of dict.
        :return: void
        """
        for row in data:
            self.add_row(row['time'], row['frame'], row['note'])

    def clear(self, *args, **kwargs):
        super(ATCenterList, self).clear(*args, **kwargs)

        # Remove Columns
        while self.columnCount() > 0:
            self.removeColumn(0)

        # Remove Rows
        while self.rowCount() > 0:
            self.removeRow(0)

        self.rowsCleared.emit()

    # ---

    def _init(self):
        # Add 4 columns if nothing
        if self.columnCount() is 0:
            for c in range(0, ATCenterList.MAX_COLS):
                self.insertColumn(0)

        # Set columns' labels
        self.setHorizontalHeaderLabels(ATCenterList.COLS_NAMES)

        # Hide columns if needed.
        self.col_interval_toggle_visibility()
        self.col_note_toggle_visibility()

    def col_interval_toggle_visibility(self):
        if self.parent.action_column_interval.isChecked():
            self.setColumnHidden(2, False)
        else:
            self.setColumnHidden(2, True)

    def col_note_toggle_visibility(self):
        if self.parent.action_column_note.isChecked():
            self.setColumnHidden(3, False)
        else:
            self.setColumnHidden(3, True)

    # ---
    # Events

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.parent.on_start_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.parent.on_stop_btn_clicked()
            event.accept()
        elif event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
            self.parent.on_reset_btn_clicked()
            event.accept()
        else:
            # Make sure usual keys get dealt with
            super(ATCenterList, self).keyPressEvent(event)

    def focusOutEvent(self, *args, **kwargs):
        # When this widget loose the focus, stop the timer
        setting = AnimationTimer.load_settings_file()
        if setting.value("Preferences/stop_timer_on_out_focus", True):
            self.parent.on_stop_btn_clicked()

        super(ATCenterList, self).focusOutEvent(*args, **kwargs)

    # ---

    @QtCore.Slot()
    def on_content_changed(self):
        if self.parent.file is None:
            if self.rowCount() > 0:
                self.changed = True
                self.parent.file_info_label.setText(u"Untitled*")
            else:
                self.changed = False
                self.parent.file_info_label.setText(u"Untitled")
        else:
            if self.export_data() == self.parent.file.data:
                self.changed = False
                self.parent.file_info_label.setText(self.parent.file.fileName())
            else:
                self.changed = True
                self.parent.file_info_label.setText(self.parent.file.fileName() + u'*')

        if self.changed:
            self.parent.action_discard_current_changes.setEnabled(True)
        else:
            self.parent.action_discard_current_changes.setEnabled(False)

        self.contentChanged.emit(self.changed)

    def on_vertical_header_clicked(self):
        """
        By clicking on the row id, it start the playback from the current frame specified on this row.
        Each click restart the playback from this frame number.
        :param logicalIndex:
        :return:
        """
        pass
        # Get the frame number for the row
        data = int(self.item(self.currentRow(), 1).text())

        # Playback
        pm.currentTime(data)

        if self.parent.sound_btn.isChecked():
            pm.play(forward=True, playSound=True)
        else:
            pm.play(forward=True, playSound=False)


class ATFile(QtCore.QFile):
    """
    File object to manage timing file.
    """
    def __init__(self, name, parent=None):
        super(ATFile, self).__init__(name, parent)
        self.parent = parent

        self.fps = None
        self.offset_time = 0
        self.offset_frame = 0
        self.data = None

    def __getitem__(self, item):
        return self.data[item]

    def save(self):
        """
        Save the file to the disk
        :return: void
        """
        # Populate the file with latest data
        self.populate()

        # Add to recent timing or update if already exists
        self.parent.recent_timings.add(self)

        # Save it to a file
        data = self._prepare_saving_data()
        with open(self.fileName(), "w") as f:
            json.dump(data, f, indent=4, separators=(',', ': '))

        # Set file changed of False
        self.parent.central_list.changed = False
        self.parent.central_list.on_content_changed()

    def load(self):
        """
        Load a file data into the app.
        :return: void
        """

        # Get data from file
        with open(self.fileName(), "r") as f:
            try:
                data = json.load(f)
            except ValueError:
                return AnimationTimer.error("This file could not be read. Is it a valid JSON file with contents ?")

        # Security
        state = self._on_load_check(data)
        if state is False:
            return

        try:
            # If no error, Reset interface
            self.parent.on_reset_btn_clicked()

            # Propagate data to file and app
            self.propagate(data)

            # Add to recent timing or update if already exists
            self.parent.recent_timings.add(self)
        except:
            return AnimationTimer.error("Cannot load the file " + self.fileName() + ". It seems corrupted.")

        if self.parent.action_timing_on_timeline.isChecked() and self.data:
            for row in self.data:
                self.parent.node.add(row['frame'])

    # ---

    def _prepare_saving_data(self):
        now = datetime.now()

        d = dict()
        d['infos'] = {
            'plugin_name': AnimationTimer.TITLE,
            'plugin_version': AnimationTimer.VERSION,
            'fps': self.fps,
            'offset_time': self.offset_time,
            'offset_frame': self.offset_frame,
            'date': '{m}/{d}/{y} {h}:{min}:{s}'.format(
                m=now.month,
                d=now.day,
                y=now.year,
                h=now.hour,
                min=now.minute,
                s=now.second,
            )
        }
        d['data'] = self.data

        return d

    def _on_load_check(self, dic):
        """
        Verify data in the file before load.
        Check for file info as : Title, Version and Date.
        Check critical info as : FPS and Offsets
        :param: dict
        :return: bool
        """
        data = dic.get('infos', None)

        plugin_name = data.get('plugin_name', None)
        plugin_version = data.get('plugin_version', None)
        fps = data.get('fps', None)
        offset_time = data.get('offset_time', None)
        offset_frame = data.get('offset_frame', None)

        # If not data whatsoever, do not load.
        if data is None:
            AnimationTimer.error("File header cannot be recovered. Data like 'fps' or 'offsets' are not available.")
            AnimationTimer.error("Load aborted.")
            return False

        if not plugin_name or plugin_name != AnimationTimer.TITLE:
            AnimationTimer.warning("The plugin title could not be found in the save file.")
            AnimationTimer.warning("Are you sure it is meant to be used in Animation Timer ?")

        if not plugin_version:
            AnimationTimer.warning("The version of this save file could not be found. Use it with caution.")

        if plugin_version < AnimationTimer.VERSION:
            AnimationTimer.error("Ancien save file are not compatible with this version of the script.")
            AnimationTimer.error("Load aborted.")
            return False

        if not fps or not isinstance(int(fps), int):
            AnimationTimer.warning("FPS data could not be found or is corrupted. Default FPS will be used.")
            AnimationTimer.info("You can still change that in the options panel.")

        if not offset_time or not isinstance(int(offset_time), int):
            AnimationTimer.warning("Offset Time data could not be found or is corrupted.")
            AnimationTimer.info("Offset Time will be set to 0.")
            AnimationTimer.info("You can still change that in the options panel.")

        if not offset_time or not isinstance(int(offset_time), int):
            AnimationTimer.warning("Offset Frame data could not be found or is corrupted.")
            AnimationTimer.info("Offset Frame will be set to 0.")
            AnimationTimer.info("You can still change that in the options panel.")

        return True

    # ---

    def populate(self):
        """
        From the app to the file.
        """
        data = self.parent.options_window.export_data()

        self.fps = data.get('fps')
        self.offset_time = data.get('offset_time')
        self.offset_frame = data.get('offset_frame')
        self.data = self.parent.central_list.export_data()

    def propagate(self, data):
        """
        From the file to the app.
        """
        # The best way is to send data to options window and then activate the accepted function.
        self.parent.options_window.restore_from_data(data)
        self.parent.options_window.on_accepted()

        # Save in ATFile too
        infos = data.get('infos', None)
        if infos:
            self.fps = infos.get('fps', AnimationTimerOptions.default_fps)
            self.offset_time = infos.get('offset_time', 0)
            self.offset_frame = infos.get('offset_frame', 0)

        self.data = data.get('data', {})

        # Import data to central_list
        self.parent.central_list.import_data(self.data)


class ATRecentTimings(object):
    """
    Manage recent timing files.
    """
    MAX = 10

    def __init__(self, parent=None):
        self.parent = parent
        self.data = list()

        settings = AnimationTimer.load_settings_file()
        self.max_count = int(settings.value("Preferences/max_recent_timing", ATRecentTimings.MAX))

        # Populate at launch from settings
        self._load()

    def __getitem__(self, item):
        return self.data[item]

    def add(self, f):
        """
        Add a recent timing to the list.
        If already exists, make it to the top of the list.
        :param f: ATFile obj
        :return: void
        """
        if f in self.data:
            self._update(f)
        else:
            if self.count >= self.max_count:
                self.data.pop()

            self.data.insert(0, f)

        # Remove Duplicates
        self._uniqify()

    def remove(self, f):
        """
        Remove a recent timing from the list.
        :param f: ATFile
        :return: bool
        """
        self.data.remove(f)

        # Remove Duplicates
        self._uniqify()

    def clear(self):
        """
        Clear the list of Recent Timings.
        :return: void
        """
        self.data[:] = []

    def all(self):
        """
        Return all the list of recent timings
        :return: list
        """
        return self.data

    # ---

    def on_clear_triggerd(self):
        """
        When clearing recent timing items.
        It is permanent. You will have to reopen a create new files to append to the list again.
        :return:
        """
        self.clear()
        self._uniqify()

    # ---

    @property
    def count(self):
        """
        Count the number of file in Recent Timings
        :return: int
        """
        return len(self.data)

    # ---

    def _update(self, f):
        """
        Update a recent timing by putting it to the top of the list.
        :param f: ATFile obj
        :return: void
        """
        self.remove(f)
        self.add(f)

        # Remove Duplicates
        self._uniqify()

    def _uniqify(self):
        """
        Remove all duplicates from data when preserving the order.
        """
        seen = set()
        result = list()

        for f in self.data:
            if f.fileName() in seen: continue
            result.append(f)
            seen.add(f.fileName())

        self.data[:] = result

        # Save changes
        self._save()

        # Automatically generate the menu
        self._generate_menu()

    def _generate_menu(self):
        """
        Generate the menu
        :return: void
        """
        if self.count > 0:
            # Enabled the submenu
            self.parent.submenu_recent_timing.setEnabled(True)

            # Delete all actions in the menu to recreate them later
            # Only temporary...
            self.parent.submenu_recent_timing.clear()

            # Add actions dynamically
            for f in self.data:
                # Create QAction
                item = QtGui.QAction(f.fileName(), self.parent)
                item.setAutoRepeat(False)
                item.triggered.connect(self.parent.on_recent_item_triggered)

                # Append to submenu
                self.parent.submenu_recent_timing.addAction(item)

            # Add management options at the bottom
            item_clear = QtGui.QAction(u"Clear", self.parent)
            item_clear.setAutoRepeat(False)
            item_clear.triggered.connect(self.on_clear_triggerd)

            self.parent.submenu_recent_timing.addSeparator()
            self.parent.submenu_recent_timing.addAction(item_clear)

        else:
            self.parent.submenu_recent_timing.setEnabled(False)

    def _save(self):
        """
        Save data to setting file.
        :return: bool
        """
        settings = AnimationTimer.load_settings_file()
        settings.beginGroup("RecentTimings")

        # Remove everything inside that group
        settings.remove('')

        # Add new data
        for key, value in enumerate(self.data):
            settings.setValue("recent_timing_" + str(key+1), value.fileName())

        settings.endGroup()

    def _load(self):
        """
        Load data from setting file.
        :return: bool
        """
        # Clear the list before hand
        self.clear()

        settings = AnimationTimer.load_settings_file()
        settings.beginGroup("RecentTimings")

        # Get all keys
        keys = settings.allKeys()

        # Populate
        if keys:
            for key in keys:
                self.data.append(ATFile(settings.value(key)))

        # Generate menu
        self._generate_menu()

        settings.endGroup()


class AnimationTimerOptions(QtGui.QDialog):

    fps_preset_list = [6, 12, 15, 24, 25, 30, 48, 50, 60]
    default_fps = 24

    MIN_FPS = 6
    MAX_FPS = 120

    def __init__(self, parent=None):
        super(AnimationTimerOptions, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle(u"Options")
        self.setFixedSize(250, 350)
        self.setModal(False)

        self.move_window()

        self.create_controls()
        self.create_layout()
        self.create_connections()

        self._read_settings()

        self.populate()

    # ---

    def create_controls(self):

        # Fonts
        self.font = QtGui.QFont()
        self.font.setBold(True)
        self.font.setPixelSize(14)

        # Separator
        self.border1 = QtGui.QFrame()
        self.border1.setFrameShape(QtGui.QFrame.HLine)
        self.border1.setStyleSheet("""
                                   color:#757575;
                                   """)

        self.border2 = QtGui.QFrame()
        self.border2.setFrameShape(QtGui.QFrame.HLine)
        self.border2.setStyleSheet("""
                                   color:#757575;
                                   """)

        self.border3 = QtGui.QFrame()
        self.border3.setFrameShape(QtGui.QFrame.HLine)
        self.border3.setStyleSheet("""
                                   color:#757575;
                                   """)

        # FPS
        self.fps_title = QtGui.QLabel(u"Frame per Second")
        self.fps_title.setFont(self.font)

        self.fps_radio_preset = QtGui.QRadioButton(u"Presets")
        self.fps_radio_preset.setFixedWidth(80)
        self.fps_radio_preset.setStyleSheet("""
                                        margin-left:15px;
                                        """)

        self.fps_radio_custom = QtGui.QRadioButton(u"Custom")
        self.fps_radio_custom.setFixedWidth(80)
        self.fps_radio_custom.setStyleSheet("""
                                        margin-left:15px;
                                        """)

        self.fps_combobox = QtGui.QComboBox()
        self.fps_combobox.setFixedWidth(100)

        self.fps_label = QtGui.QLabel(u"fps")
        self.custom_fps_label = QtGui.QLabel(u"fps")

        self.fps_custom_spinbox = QtGui.QSpinBox()
        self.fps_custom_spinbox.setRange(
            AnimationTimerOptions.MIN_FPS, AnimationTimerOptions.MAX_FPS)
        self.fps_custom_spinbox.setFixedWidth(100)
        self.fps_custom_spinbox.setButtonSymbols(
            QtGui.QAbstractSpinBox.NoButtons)
        self.fps_custom_spinbox.setSingleStep(2)

        # Offset Time
        self.offset_time_title = QtGui.QLabel(u"Offset Time")
        self.offset_time_title.setFont(self.font)
        self.offset_time_title.setStyleSheet("""
                                             margin-top:20px;
                                             """)

        self.timebox = QtGui.QTimeEdit()
        self.timebox.setMinimumTime(QtCore.QTime(0, 0, 0, 0))
        self.timebox.setMaximumTime(QtCore.QTime(0, 60, 0, 0))
        self.timebox.setDisplayFormat("mm:ss:zzz")

        self.offset_time_eraser = QtGui.QPushButton()
        self.offset_time_eraser.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'at_eraser.png')).path()).pixmap(16, 16))
        self.offset_time_eraser.setFlat(True)
        self.offset_time_eraser.setIconSize(QtCore.QSize(10, 10))
        self.offset_time_eraser.setFixedSize(16, 16)
        self.offset_time_eraser.setStatusTip(u"Clear the timer's offset.")

        # Offset Frame
        self.offset_frame_title = QtGui.QLabel(u"Offset Frame")
        self.offset_frame_title.setFont(self.font)
        self.offset_frame_title.setStyleSheet("""
                                             margin-top:20px;
                                             """)

        self.framebox = QtGui.QSpinBox()
        self.framebox.setMinimum(0)
        self.framebox.setSingleStep(1)
        self.framebox.setMaximum(99999)

        self.offset_frame_eraser = QtGui.QPushButton()
        self.offset_frame_eraser.setIcon(QtGui.QIcon(QtCore.QDir(os.path.join(AnimationTimer.ICON_DIR, 'at_eraser.png')).path()).pixmap(16, 16))
        self.offset_frame_eraser.setFlat(True)
        self.offset_frame_eraser.setIconSize(QtCore.QSize(10, 10))
        self.offset_frame_eraser.setFixedSize(16, 16)
        self.offset_frame_eraser.setStatusTip(u"Clear the frame offset.")

        # Button Box
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                                 QtGui.QDialogButtonBox.Cancel)
        self.button_box.setCenterButtons(True)
        self.button_box.setStyleSheet("""
                                      margin-top:15px;
                                      width:48%;
                                      padding:4px 6px;
                                      """)

    def create_layout(self):

        # FPS Layout
        fps_layout = QtGui.QHBoxLayout()
        fps_layout.addWidget(self.fps_radio_preset)
        fps_layout.addWidget(self.fps_combobox)
        fps_layout.addWidget(self.fps_label)

        fps_custom_layout = QtGui.QHBoxLayout()
        fps_custom_layout.addWidget(self.fps_radio_custom)
        fps_custom_layout.addWidget(self.fps_custom_spinbox)
        fps_custom_layout.addWidget(self.custom_fps_label)

        # Offset Time
        offset_time_layout = QtGui.QHBoxLayout()
        offset_time_layout.addWidget(self.timebox)
        offset_time_layout.addWidget(self.offset_time_eraser)

        # Offset Frame
        offset_frame_layout = QtGui.QHBoxLayout()
        offset_frame_layout.addWidget(self.framebox)
        offset_frame_layout.addWidget(self.offset_frame_eraser)

        # Main layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.fps_title)
        main_layout.addWidget(self.border1)
        main_layout.addLayout(fps_layout)
        main_layout.addLayout(fps_custom_layout)
        main_layout.addWidget(self.offset_time_title)
        main_layout.addWidget(self.border2)
        main_layout.addLayout(offset_time_layout)
        main_layout.addWidget(self.offset_frame_title)
        main_layout.addWidget(self.border3)
        main_layout.addLayout(offset_frame_layout)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def create_connections(self):
        self.button_box.accepted.connect(self.on_accepted)
        self.button_box.rejected.connect(self.on_rejected)

        self.fps_radio_preset.clicked.connect(self.on_fps_preset_selected)
        self.fps_radio_custom.clicked.connect(self.on_fps_custom_selected)

        self.offset_time_eraser.clicked.connect(self.on_clear_offset_time_clicked)
        self.offset_frame_eraser.clicked.connect(self.on_clear_offset_frame_clicked)

    def populate(self):
        """
        Populate on creation.
        """

        # FPS
        for x in AnimationTimerOptions.fps_preset_list:
            self.fps_combobox.addItem(str(x))

        self.fps_radio_preset.setChecked(True)
        self.on_fps_preset_selected()

    # ---

    def move_window(self):

        # Position on the right edge
        x = self.parent.x() + self.parent.frameGeometry().width() + 20
        y = self.parent.y()

        # Get screen resolution
        desk = QtGui.QDesktopWidget().screenGeometry()

        # Calculate the most distant point in x when the options window is open.
        fx = x + self.width()

        # If position make it outside of the screen, pop it to the left instead.
        if fx > desk.width():
            x = self.parent.x() - 20 - self.width()

        self.move(x, y)

    # ---

    def on_accepted(self):
        # FPS
        if self.fps_radio_preset.isChecked():
            self.fps = int(self.fps_combobox.currentText())

        if self.fps_radio_custom.isChecked():
            self.fps = int(self.fps_custom_spinbox.value())

        # Change on the interface
        self.parent.fps_label.setNum(self.fps)

        # Offsets
        offset_time_ms = QtCore.QTime(0, 0, 0).msecsTo(self.timebox.time())
        offset_frame_ms = AnimationTimer.calculate_time_ms(self.framebox.value(), self.parent.fps_label.text())
        self.parent.timer.offset = int(offset_time_ms + offset_frame_ms)
        self.parent.timer_label.setText(QtCore.QTime(0, 0, 0).addMSecs(self.parent.timer.offset).toString("mm:ss:zzz"))

        self.parent.frame_counter_label.setNum(int(AnimationTimer.calculate_frames(self.parent.timer.offset, self.fps)))

        if self.parent.timer.offset > 0:
            self.parent.action_reset_offsets.setEnabled(True)

        return self.accept()

    def on_rejected(self):
        return self.reject()

    # ---

    def on_fps_preset_selected(self):
        self.fps_combobox.setEnabled(True)
        self.fps_custom_spinbox.setEnabled(False)
        self.fps_label.setStyleSheet("""
                                     color:#C8C8C8;
                                     """)
        self.fps_radio_preset.setStyleSheet("""
                                            color:#C8C8C8;
                                            margin-left:15px;
                                            """)
        self.fps_radio_custom.setStyleSheet("""
                                            color:#707070;
                                            margin-left:15px;
                                            """)
        self.custom_fps_label.setStyleSheet("""
                                            color:#707070;
                                            """)

    def on_fps_custom_selected(self):
        self.fps_combobox.setEnabled(False)
        self.fps_custom_spinbox.setEnabled(True)

        self.fps_label.setStyleSheet("""
                                     color:#707070;
                                     """)
        self.fps_radio_preset.setStyleSheet("""
                                            color:#707070;
                                            margin-left:15px;
                                            """)
        self.fps_radio_custom.setStyleSheet("""
                                            color:#C8C8C8;
                                            margin-left:15px;
                                            """)
        self.custom_fps_label.setStyleSheet("""
                                            color:#C8C8C8;
                                            """)

    def on_clear_offset_time_clicked(self):
        self.timebox.setTime(QtCore.QTime(0, 0, 0, 0))

    def on_clear_offset_frame_clicked(self):
        self.framebox.setValue(0)

    def export_data(self):
        """
        Data exported are FPS and OFFSETS (Time & Frame)
        :return: dict
        """
        d = dict()
        d['fps'] = self.parent.fps_label.text()
        d['offset_time'] = QtCore.QTime(0, 0, 0).msecsTo(self.timebox.time())
        d['offset_frame'] = self.framebox.value()

        return d

    def restore_from_data(self, data):
        """
        Get a dict of data and restore the application from this data.
        :param data: dict
        :return:
        """
        infos = data.get('infos', None)

        if not infos:
            return

        # FPS
        fps = infos.get('fps', AnimationTimerOptions.default_fps)
        if AnimationTimerOptions.is_preset(int(fps)):
            self.on_fps_preset_selected()
            i = self.fps_combobox.findText(str(fps))
            self.fps_combobox.setCurrentIndex(i)
        else:
            self.on_fps_custom_selected()
            self.fps_custom_spinbox.setValue(int(fps))

        # Offsets
        offset_time = infos.get('offset_time', 0)
        offset_frame = infos.get('offset_frame', 0)

        self.timebox.setTime(QtCore.QTime(0, 0, 0, 0).addMSecs(offset_time))
        self.framebox.setValue(int(offset_frame))

    # ---

    @classmethod
    def is_preset(cls, fps):
        """
        Check if a fps number is a preset or a custom.
        :return bool
        """
        return True if fps in AnimationTimerOptions.fps_preset_list else False

    # ---

    def _read_settings(self):
        settings = AnimationTimer.load_settings_file()
        AnimationTimerOptions.default_fps = settings.value("Preferences/default_fps", 24)


class AnimationTimerPreferences(QtGui.QDialog):

    def __init__(self, parent):
        super(AnimationTimerPreferences, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle(u"Preferences")
        self.setFixedSize(400, 350)

        self.create_layout()
        self.create_connections()

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
        self.menu_list.addItem(u'Timings')
        self.menu_list.setCurrentRow(0)
        self.menu_list.setStyleSheet("background-color:#191919;")

        # Set Default FPS
        self.default_custom_fps_spinbox = QtGui.QSpinBox()
        self.default_custom_fps_spinbox.setRange(
            AnimationTimerOptions.MIN_FPS, AnimationTimerOptions.MAX_FPS)
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

        # Set Default Width / height
        self.default_mainwindow_width = QtGui.QSpinBox()
        self.default_mainwindow_width.setRange(self.parent.minimumWidth(), self.parent.maximumWidth())
        self.default_mainwindow_width.setSingleStep(1)

        self.default_mainwindow_height = QtGui.QSpinBox()
        self.default_mainwindow_height.setRange(self.parent.minimumHeight(), self.parent.maximumHeight())
        self.default_mainwindow_height.setSingleStep(1)

        self.default_mainwindow_width_label = QtGui.QLabel(u"Width")
        self.default_mainwindow_height_label = QtGui.QLabel(u"Height")

        self.default_mainwindow_separator = QtGui.QLabel(u"/")

        self.default_mainwindow_size_grid = QtGui.QGridLayout()
        self.default_mainwindow_size_grid.addWidget(
            self.default_mainwindow_width_label, 0, 0
        )
        self.default_mainwindow_size_grid.addWidget(
            self.default_mainwindow_height_label, 0, 2
        )
        self.default_mainwindow_size_grid.addWidget(
            self.default_mainwindow_width, 1, 0
        )
        self.default_mainwindow_size_grid.addWidget(
            self.default_mainwindow_separator, 1, 1, QtCore.Qt.AlignCenter
        )
        self.default_mainwindow_size_grid.addWidget(
            self.default_mainwindow_height, 1, 2
        )

        self.default_mainwindow_size_group = QtGui.QGroupBox(u"Default Main Window Size")
        self.default_mainwindow_size_group.setLayout(self.default_mainwindow_size_grid)
        self.default_mainwindow_size_group.setSizePolicy(policy)

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

        self.project_save_in_dirs_vbox = QtGui.QVBoxLayout()
        self.project_save_in_dirs_vbox.addWidget(self.project_save_in_dirs)

        self.project_save_in_dirs_group = QtGui.QGroupBox(
            u'Projects')
        self.project_save_in_dirs_group.setLayout(self.project_save_in_dirs_vbox)

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
        self.vbox_general.addWidget(self.auto_load_timing_group)

        self.tab_general = QtGui.QWidget()
        self.tab_general.setLayout(self.vbox_general)

        # Timings tab
        self.vbox_project = QtGui.QVBoxLayout()
        self.vbox_project.setAlignment(QtCore.Qt.AlignTop)
        self.vbox_project.addWidget(self.default_dir_group)
        self.vbox_project.addWidget(self.project_save_in_dirs_group)
        self.vbox_project.addWidget(self.recent_timing_group)

        self.tab_project = QtGui.QWidget()
        self.tab_project.setLayout(self.vbox_project)

        # Stacked the *pages*
        self.menu_stacked = QtGui.QStackedWidget()
        self.menu_stacked.addWidget(self.tab_general)
        self.menu_stacked.addWidget(self.tab_project)

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

    # ---

    def on_accepted(self):
        self._write_pref_settings()
        return self.accept()

    def on_rejected(self):
        return self.reject()

    # ---

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

    # ---

    def _read_pref_settings(self):
        settings = AnimationTimer.load_settings_file()

        settings.beginGroup("Preferences")

        # General
        self.default_custom_fps_spinbox.setValue(
            int(settings.value("default_fps", 24)))

        directory = QtCore.QDir(
            settings.value(
                "default_directory",
                QtCore.QDir.homePath()))
        self.default_dir_lineedit.setText(directory.path())

        self.recent_timing_spinbox.setValue(
            int(settings.value("max_recent_timing", 10)))

        self.auto_load_timing.setChecked(
            bool_str(settings.value("auto_load_last_timing", False)))

        self.project_save_in_dirs.setChecked(
            bool_str(settings.value("project_save_in_dirs", True)))

        settings.endGroup()

    def _write_pref_settings(self):
        settings = AnimationTimer.load_settings_file()

        settings.beginGroup("Preferences")

        # For directory, passes it to QDir for multi-system
        directory = QtCore.QDir(self.default_dir_lineedit.text())

        settings.setValue("default_fps", self.default_custom_fps_spinbox.value())
        settings.setValue("default_directory", directory.path())
        settings.setValue("max_recent_timing", self.recent_timing_spinbox.value())
        settings.setValue("auto_load_last_timing", self.auto_load_timing.isChecked())
        settings.setValue("project_save_in_dirs", self.project_save_in_dirs.isChecked())

        settings.endGroup()


class ATNode(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.name = "AnimationTimerFrames"

        self.keys = list()

        self._node = None

    def __nonzero__(self):
        return True if self.__len__ > 0 else False

    def __len__(self):
        return len(self.keys)

    def __iter__(self):
        for item in self.keys:
            yield item

    def create(self):
        """
        Create the object in Maya
        """
        # Delete it if exists
        self.delete()

        # Create it
        pm.group(w=True, em=True, n=self.name)
        self._node = pm.general.PyNode(self.name)

        # Prepare...
        self._prepare_object()

        # If central list have content
        if self.parent.central_list.rowCount() > 0:
            data = self.parent.central_list.export_data()
            for row in data:
                self.add(row['frame'])

    def delete(self):
        """
        Delete the object in Maya
        """
        if self.exists():
            pm.delete(self.name)

    def select(self):
        """
        Select the object in Maya
        """
        return pm.select(self.name)

    def exists(self):
        """
        Is the object exists ?
        """
        return True if pm.objExists(self.name) else False

    # ---

    def add(self, frame):
        """
        Add a keyframe.
        """
        pm.setKeyframe(self.name, attribute="keys", t=frame)

    def key(self):
        pass

    def next(self):
        pass

    def previous(self):
        pass

    # ---

    def _prepare_object(self):
        """
        Prepare the attribute of the object for the keys.
        """
        pm.addAttr(self.name, longName="keys", at='bool', k=True)

        # Hide the others
        self._node.translateX.set(keyable=False)
        self._node.translateY.set(keyable=False)
        self._node.translateZ.set(keyable=False)
        self._node.rotateX.set(keyable=False)
        self._node.rotateY.set(keyable=False)
        self._node.rotateZ.set(keyable=False)
        self._node.scaleX.set(keyable=False)
        self._node.scaleY.set(keyable=False)
        self._node.scaleZ.set(keyable=False)
        self._node.visibility.set(keyable=False)

        self._node.translateX.set(channelBox=False)
        self._node.translateY.set(channelBox=False)
        self._node.translateZ.set(channelBox=False)
        self._node.rotateX.set(channelBox=False)
        self._node.rotateY.set(channelBox=False)
        self._node.rotateZ.set(channelBox=False)
        self._node.scaleX.set(channelBox=False)
        self._node.scaleY.set(channelBox=False)
        self._node.scaleZ.set(channelBox=False)
        self._node.visibility.set(channelBox=False)


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
