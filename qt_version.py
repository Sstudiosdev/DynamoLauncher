from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt, QSettings
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QComboBox, QSpacerItem, QSizePolicy, QProgressBar, QPushButton, QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QPixmap
from os.path import join, isdir
from PyQt5.QtGui import QPixmap, QIcon
import os

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command

from random_username.generate import generate_username
from uuid import uuid1

from subprocess import call
from sys import argv, exit

minecraft_directory = get_minecraft_directory().replace('minecraft', 'mjnlauncher')

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

        install_minecraft_version(versionid=self.version_id, minecraft_directory=minecraft_directory, callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })

        if self.username == '':
            self.username = generate_username()[0]
        
        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }

        call(get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options))
        self.state_update_signal.emit(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(300, 283)
        self.centralwidget = QWidget(self)

        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QSize(256, 37))
        self.logo.setText('')
        self.logo.setPixmap(QPixmap('assets/title.png'))
        self.logo.setScaledContents(True)

        # Establecer el ícono de la ventana
        self.setWindowIcon(QIcon('assets/215446.ico'))

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Username')

        self.version_select = QComboBox(self.centralwidget)
        self.version_select.addItem("Available Minecraft Versions")  # Opción predeterminada
        self.load_available_versions()  # Llamada a la función para cargar las versiones disponibles

        self.downloaded_version_select = QComboBox(self.centralwidget)
        self.downloaded_version_select.addItem("Downloaded Minecraft Versions")  # Opción predeterminada
        self.load_downloaded_versions()  # Llamada a la función para cargar las versiones descargadas

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

        self.history_button = QPushButton(self.centralwidget)
        self.history_button.setText('User History')
        self.history_button.clicked.connect(self.show_user_history)

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

        # Cargar el nombre de usuario guardado
        self.load_username()

        # Historial de nombres de usuario
        self.history = []

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
        # Obtiene la lista de versiones disponibles, excluyendo snapshots, pre-releases, alpha y beta
        available_versions = sorted(
            [version['id'] for version in get_version_list() if 
             'snapshot' not in version['type'].lower() and 
             'pre' not in version['type'].lower() and 
             'alpha' not in version['type'].lower() and 
             'beta' not in version['type'].lower()],
            key=self.version_sort_key
        )

        # Llena el ComboBox con las versiones disponibles
        self.version_select.clear()
        self.version_select.addItem("Available Minecraft Versions")  # Opción predeterminada
        self.version_select.addItems(available_versions)

    def load_downloaded_versions(self):
        # Obtiene la ruta de la carpeta de versiones de Minecraft
        versions_folder = join(minecraft_directory, 'versions')

        # Obtiene las carpetas de versiones instaladas
        downloaded_versions = sorted([f for f in os.listdir(versions_folder) if isdir(join(versions_folder, f))], key=self.version_sort_key)

        # Llena el ComboBox con las versiones instaladas
        self.downloaded_version_select.clear()
        self.downloaded_version_select.addItem("Downloaded Minecraft Versions")  # Opción predeterminada
        self.downloaded_version_select.addItems(downloaded_versions)

    def version_sort_key(self, version):
        # Función de clave para ordenar versiones
        try:
            # Intenta convertir las partes de la versión a enteros
            return tuple(map(int, version.split('.')))
        except ValueError:
            # Si hay un error al convertir a enteros, devuelve una tupla vacía
            return tuple()

    def launch_game(self):
        # Guardar el nombre de usuario antes de lanzar el juego
        self.save_username()

        # Verificar si se ha seleccionado una versión
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

def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    window = MainWindow()
    window.show()

    exit(app.exec_())

if __name__ == '__main__':
    main()
