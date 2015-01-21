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
        self.resize(600, 370)
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
        action_preferences.triggered.connect(self.open_preferences_window)

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
        action_about.triggered.connect(self.open_about_window)

        # Create the menu
        menubar = self.menuBar()

        # File menu
        menu_file = menubar.addMenu("File")
        # menu_file.addAction(action_new)
        menu_file.addAction(action_open)
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
        self.font_timer = QtGui.QFont()
        self.font_timer.setPixelSize(36)

        self.timer_visual = QtGui.QPushButton("00:00:00")
        self.timer_visual.setFlat(True)
        self.timer_visual.setFont(self.font_timer)
        self.timer_visual.setFixedHeight(50)

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

        combobox_layout = QtGui.QHBoxLayout()
        combobox_layout.setContentsMargins(10, 0, 0, 0)
        combobox_layout.setAlignment(QtCore.Qt.AlignLeft)
        combobox_layout.addWidget(self.fps)

        timing_option_layout = QtGui.QHBoxLayout()
        timing_option_layout.setContentsMargins(0, 0, 10, 0)
        timing_option_layout.setAlignment(QtCore.Qt.AlignRight)
        timing_option_layout.addWidget(self.timing_option_btn)

        # Controls Layer
        controls_layer = QtGui.QHBoxLayout()
        controls_layer.addLayout(combobox_layout)
        controls_layer.addLayout(buttons_layout)
        controls_layer.addLayout(timing_option_layout)

        # Timer Layout
        timer_layout = QtGui.QHBoxLayout()
        timer_layout.setAlignment(QtCore.Qt.AlignCenter)
        timer_layout.addWidget(self.timer_visual)

        # spacer_layout = QtGui.QHBoxLayout()
        # spacer_layout.setContentsMargins(10, 0, 0, 0)
        # spacer_layout.setAlignment(QtCore.Qt.AlignLeft)
        # spacer_layout.addWidget(spacer_item)

        frames_layout = QtGui.QHBoxLayout()
        frames_layout.setContentsMargins(0, 0, 10, 0)
        frames_layout.setAlignment(QtCore.Qt.AlignRight)
        frames_layout.addWidget(self.frames)

        # Timer Layer
        timer_bar_layout = QtGui.QHBoxLayout()
        timer_bar_layout.addStretch(1)
        timer_bar_layout.addLayout(timer_layout)
        timer_bar_layout.addLayout(frames_layout, 1)

        # Set the Main Layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(0, 6, 0, 10)
        main_layout.addLayout(timer_bar_layout)
        main_layout.addWidget(self.central_list)
        main_layout.addLayout(controls_layer)

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

    @classmethod
    def _load_settings_file(cls):
        return QtCore.QSettings(QtCore.QSettings.IniFormat,
                                QtCore.QSettings.UserScope,
                                u'yannschmidt',
                                u'Animation Timer')


class AnimationTimer(object):
    pass


class ATPreferencesWindow(QtGui.QDialog):

    def __init__(self, parent):
        super(ATPreferencesWindow, self).__init__(parent)

        self.setWindowTitle(u'Preferences')
        self.setFixedSize(400, 350)

        self.create_layout()
        self.create_connections()

        self.settings = AnimationTimerUI._load_settings_file()
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
        self.menu_list.setCurrentRow(0)
        self.menu_list.setStyleSheet("background-color:#191919;")

        # Timer option
        self.frame_default = QtGui.QRadioButton(u"Frame : 0", self)
        self.time_default = QtGui.QRadioButton(u"Time : 00:00:00", self)

        self.mode_option_vbox = QtGui.QHBoxLayout()
        self.mode_option_vbox.addWidget(self.time_default)
        self.mode_option_vbox.addWidget(self.frame_default)

        self.timer_option_group = QtGui.QGroupBox(u'Default Timer')
        self.timer_option_group.setLayout(self.mode_option_vbox)

        # Remember project
        self.timeline_fps = QtGui.QCheckBox(
            u"Set current scene FPS as default.")
        self.autorised_custom_fps = QtGui.QCheckBox(
            u"Autorised custom FPS.")

        self.project_option_vbox = QtGui.QVBoxLayout()
        self.project_option_vbox.addWidget(self.timeline_fps)
        self.project_option_vbox.addWidget(self.autorised_custom_fps)

        self.project_group = QtGui.QGroupBox(u'Project')
        self.project_group.setLayout(self.project_option_vbox)

        # Keys on Maya Timeline
        self.timeline_keys = QtGui.QCheckBox(
            u"Show keys on Maya Timeline.")

        self.timeline_option_vbox = QtGui.QVBoxLayout()
        self.timeline_option_vbox.addWidget(self.timeline_keys)

        self.timeline_option_group = QtGui.QGroupBox(u'Timeline')
        self.timeline_option_group.setLayout(self.timeline_option_vbox)

        #  Button Box
        # -----------
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                                 QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.on_reject)

        # Set Layouts

        # General tab
        self.vbox_general = QtGui.QVBoxLayout()
        self.vbox_general.setAlignment(QtCore.Qt.AlignTop)
        self.vbox_general.addWidget(self.timer_option_group)
        self.vbox_general.addWidget(self.project_group)
        self.vbox_general.addWidget(self.timeline_option_group)

        self.tab_general = QtGui.QWidget()
        self.tab_general.setLayout(self.vbox_general)

        # Stacked the *pages*
        self.menu_stacked = QtGui.QStackedWidget()
        self.menu_stacked.addWidget(self.tab_general)

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

    def on_accept(self):
        self._write_pref_settings()
        self.accept()
        return

    def on_reject(self):
        self.reject()
        return

    # SLOTS
    # -----
    def _change_current_tab(self):
        row = self.menu_list.currentRow()
        self.menu_stacked.setCurrentIndex(row)
        pass

    # Settings
    # --------

    def _read_pref_settings(self):
        pass

    def _write_pref_settings(self):
        pass


class CenterList(QtGui.QListView):

    def __init__(self, parent=None):
        super(CenterList, self).__init__(parent)

        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        # Model
        self.model = QtGui.QStandardItemModel(self)
        # self.model.setRowCount(CenterList.size())
        # Headers
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
        self.model.crear()


class FPSComboBox(QtGui.QComboBox):

    def __init__(self, parent):
        super(FPSComboBox, self).__init__(parent)

        self._load()

    def _load(self):

        self.addItem(u"6 fps")
        self.addItem(u"12 fps")
        self.addItem(u"24 fps")
        self.addItem(u"25 fps")
        self.addItem(u"30 fps")

        disable = [5]
        for i in disable:
            j = self.model().index(i, 0)
            self.model().setData(j, 0, QtCore.Qt.UserRole-1)


class QFrameColor(QtGui.QFrame):

    lightness_changed = QtCore.Signal(int)
    alpha_changed = QtCore.Signal(int)

    def __init__(self, parent):
        super(QFrameColor, self).__init__(parent)

        self.setFixedWidth(50)

        self.color = QtGui.QColor(0, 0, 0)

    def mousePressEvent(self, event):
        dialog = QtGui.QColorDialog()
        color = dialog.getColor(self.color)

        if color.isValid():
            self.color = color
            self.setStyleSheet("background-color: %s"
                               % self.color.name())
            hue, satuation, lightness, alpha = self.color.getHsl()
            self.lightness_changed.emit(lightness)

    def getColor(self, type=None):
        """
        Get the color as a QColor object.

        If type is specified:
            rgba: Return the rgba of the color
            name: Return the name as #RRGGBB
        """
        if isinstance(self.color, QtGui.QColor):
            if type is 'rgba':
                return self.color.getRgb()
            elif type is 'name':
                return self.color.name()
            else:
                return self.color

    def setColor(self, color):
        """
        Set the QColor of the frame from a QColor object.
        """
        if isinstance(color, QtGui.QColor) and color.isValid():
            self.color = color
            self._update_frame_to_current()
            self._update_slider_to_current()

    def setColorAsName(self, color):
        """
        Set the Qcolor of the frame from a name as #RRGGBB
        """
        if isinstance(color, str):
            if color.startwith('#'):
                self.color.setNamedColor(color)
                self._update_frame_to_current()
                self._update_slider_to_current()

    def setColorAsRgba(self, rgba):
        """
        Set the Qcolor of the frame from RGBA values.

        rgba: List of int values
        """
        if isinstance(rgba, list):
            list_result = []
            for r in rgba:
                list_result.append(int(r))

            red, green, blue, alpha = list_result
            self.color.setRgb(red, green, blue, alpha)
            self._update_frame_to_current()
            self._update_slider_to_current()
            self._update_transparency_ui()

    def setLightness(self, value):
        """
        Set the lightness of the color

        value: Between 0 and 255
        """
        if isinstance(value, int) and value in range(0, 256):
            hue, saturation, lightness, alpha = self.color.getHsl()
            self.color.setHsl(hue, saturation, value)
            self._update_frame_to_current()

    def setAlpha(self, value):
        """
        Set the lightness of the color

        value: Between 0 and 255
        """
        if isinstance(value, int) and value in range(0, 256):
            self.color.setAlpha(value)

    def _update_frame_to_current(self):
        self.setStyleSheet("background-color: %s"
                           % self.color.name())

    def _update_slider_to_current(self):
        hue, satuation, lightness, alpha = self.color.getHsl()
        self.lightness_changed.emit(lightness)

    def _update_transparency_ui(self):
        hue, satuation, lightness, alpha = self.color.getHsl()
        self.alpha_changed.emit(alpha)


if __name__ == "__main__":

    try:
        ui.close()
    except:
        pass

    ui = AnimationTimerUI()
    ui.show()
