from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt, QSettings
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QSpacerItem,
    QSizePolicy, QProgressBar, QPushButton, QApplication, QMainWindow,
    QMessageBox, QDialog, QCheckBox, QMenuBar, QAction
)
from PyQt5.QtGui import QPixmap, QIcon

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command

from random_username.generate import generate_username
from uuid import uuid1

from subprocess import Popen, CREATE_NO_WINDOW
from os.path import join, isdir
import os

minecraft_directory = get_minecraft_directory().replace('minecraft', 'DynamoLauncher')


class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    version_id = ''
    username = ''

    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username):
        self.version_id = version_id
        self.username = username

    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):
        self.state_update_signal.emit(True)

        install_minecraft_version(
            versionid=self.version_id,
            minecraft_directory=minecraft_directory,
            callback={
                'setStatus': self.update_progress_label,
                'setProgress': self.update_progress,
                'setMax': self.update_progress_max
            }
        )

        if not self.username:
            self.username = generate_username()[0]

        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }

        process = Popen(
            get_minecraft_command(
                version=self.version_id,
                minecraft_directory=minecraft_directory,
                options=options
            ),
            creationflags=CREATE_NO_WINDOW
        )
        process.wait()
        self.state_update_signal.emit(False)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)

        self.setWindowTitle("Configuración")
        self.setGeometry(parent.geometry().center().x() - 150, parent.geometry().center().y() - 150, 300, 300)

        self.dark_mode_checkbox = QCheckBox("Modo oscuro", self)
        self.dark_mode_checkbox.setChecked(parent.dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(parent.toggle_dark_mode)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.dark_mode_checkbox)

        self.apply_button = QPushButton("Aplicar", self)
        self.apply_button.clicked.connect(self.apply_changes)

        self.close_button = QPushButton("Cerrar", self)
        self.close_button.clicked.connect(self.close_dialog)

        self.layout.addWidget(self.apply_button)
        self.layout.addWidget(self.close_button)

        self.save_changes = False

    def apply_changes(self):
        self.save_changes = True
        self.accept()

    def close_dialog(self):
        if not self.save_changes:
            self.dark_mode_checkbox.setChecked(not self.dark_mode_checkbox.isChecked())

        self.reject()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dark_mode = False

        self.resize(300, 283)
        self.centralwidget = QWidget(self)

        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QSize(256, 37))
        self.logo.setText('')
        self.logo.setPixmap(QPixmap('assets/title.png'))
        self.logo.setScaledContents(True)

        self.setWindowIcon(QIcon('assets/215446.ico'))
        self.setWindowTitle("DynamoLauncher V1.1")

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        line_edit_style = (
            "QLineEdit {"
            "   background-color: #ecf0f1;"
            "   border: 1px solid #bdc3c7;"
            "   border-radius: 4px;"
            "   padding: 5px;"
            "}"
        )

        combo_box_style = (
            "QComboBox {"
            "   background-color: #ecf0f1;"
            "   border: 1px solid #bdc3c7;"
            "   border-radius: 4px;"
            "   padding: 5px;"
            "}"
        )

        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Username')
        self.username.setStyleSheet(line_edit_style)

        self.version_select = QComboBox(self.centralwidget)
        self.version_select.addItem("Available Minecraft Versions")
        self.load_available_versions()
        self.version_select.setStyleSheet(combo_box_style)

        self.downloaded_version_select = QComboBox(self.centralwidget)
        self.downloaded_version_select.addItem("Downloaded Minecraft Versions")
        self.load_downloaded_versions()
        self.downloaded_version_select.setStyleSheet(combo_box_style)

        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)

        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 24)
        self.start_progress.setVisible(False)

        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Play')
        self.start_button.clicked.connect(self.launch_game)
        self.apply_button_style(self.start_button)

        self.history_button = QPushButton(self.centralwidget)
        self.history_button.setText('User History')
        self.history_button.clicked.connect(self.show_user_history)
        self.apply_button_style(self.history_button)

        self.vertical_layout = QVBoxLayout(self.centralwidget)
        self.vertical_layout.setContentsMargins(15, 15, 15, 15)
        self.vertical_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vertical_layout.addItem(self.titlespacer)
        self.vertical_layout.addWidget(self.username)
        self.vertical_layout.addWidget(self.version_select)
        self.vertical_layout.addWidget(self.downloaded_version_select)
        self.vertical_layout.addItem(self.progress_spacer)
        self.vertical_layout.addWidget(self.start_progress_label)
        self.vertical_layout.addWidget(self.start_progress)
        self.vertical_layout.addWidget(self.start_button)
        self.vertical_layout.addWidget(self.history_button)

        self.launch_thread = LaunchThread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)

        self.setCentralWidget(self.centralwidget)

        self.load_username()
        self.history = []

        self.menuBar().setNativeMenuBar(False)
        self.settings_menu = self.menuBar().addMenu("Configuración")

        self.open_settings_action = QAction("Abrir Configuración", self)
        self.open_settings_action.triggered.connect(self.open_settings_dialog)
        self.settings_menu.addAction(self.open_settings_action)

    def load_username(self):
        settings = QSettings('TuOrganizacion', 'TuAplicacion')
        saved_username = settings.value('username', '')
        if saved_username:
            self.username.setText(saved_username)

    def save_username(self):
        username = self.username.text()
        if username:
            self.history.append(username)
            settings = QSettings('TuOrganizacion', 'TuAplicacion')
            settings.setValue('username', username)

    def show_user_history(self):
        history_text = "\n".join(self.history)
        message_box = QMessageBox()
        message_box.setWindowTitle("User History")
        message_box.setText("Usernames used:\n" + history_text)
        message_box.exec_()

    def state_update(self, value):
        self.start_button.setDisabled(value)
        self.start_progress_label.setVisible(value)
        self.start_progress.setVisible(value)

    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label)

    def load_available_versions(self):
        available_versions = sorted(
            [version['id'] for version in get_version_list() if
             'snapshot' not in version['type'].lower() and
             'pre' not in version['type'].lower() and
             'alpha' not in version['type'].lower() and
             'beta' not in version['type'].lower()],
            key=self.version_sort_key
        )

        self.version_select.clear()
        self.version_select.addItem("Available Minecraft Versions")
        self.version_select.addItems(available_versions)

    def load_downloaded_versions(self):
        versions_folder = join(minecraft_directory, 'versions')

        try:
            downloaded_versions = sorted([f for f in os.listdir(versions_folder) if isdir(join(versions_folder, f))],
                                         key=self.version_sort_key)
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning",
                                "Minecraft versions folder not found. Make sure DynamoLauncher is set up correctly.")
            return

        self.downloaded_version_select.clear()
        self.downloaded_version_select.addItem("Downloaded Minecraft Versions")
        self.downloaded_version_select.addItems(downloaded_versions)

    def version_sort_key(self, version):
        try:
            return tuple(map(int, version.split('.')))
        except ValueError:
            return tuple()

    def launch_game(self):
        self.save_username()

        selected_version = None
        if self.version_select.currentIndex() > 0:
            selected_version = self.version_select.currentText()
        elif self.downloaded_version_select.currentIndex() > 0:
            selected_version = self.downloaded_version_select.currentText()

        if selected_version is None:
            QMessageBox.warning(self, "Warning", "Please select a Minecraft version.")
            return

        self.launch_thread.launch_setup_signal.emit(selected_version, self.username.text())
        self.launch_thread.start()

    def apply_button_style(self, button):
        button_style = (
            "QPushButton {"
            "   background-color: #0072f5;"
            "   border: none;"
            "   color: white;"
            "   padding: 10px 20px;"
            "   text-align: center;"
            "   text-decoration: none;"
            "   font-size: 16px;"
            "   margin: 4px 2px;"
            "   border-radius: 8px;"
            "}"
            "QPushButton:hover {"
            "   background-color: #1471db;"
            "}"
        )
        button.setStyleSheet(button_style)

    def open_settings_dialog(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()

    def toggle_dark_mode(self, state):
        self.dark_mode = state == Qt.CheckState.Checked
        self.update_theme()

    def update_theme(self):
        if self.dark_mode:
            self.centralwidget.setStyleSheet(
                "background-color: #2e2e2e;"
                "color: #ffffff;"
            )
        else:
            self.centralwidget.setStyleSheet(
                "background-color: #ffffff;"
                "color: #000000;"
            )


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    
    app = QApplication([])
    window = MainWindow()
    window.showMaximized()
    exit(app.exec_())


if __name__ == '__main__':
    main()

# MIT License

# Copyright (c) 2023 Sstudios
