import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

class MinecraftLauncher(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Configuración de la ventana principal
        self.setGeometry(100, 100, 300, 200)
        self.setWindowTitle('Minecraft Launcher')

        # Etiqueta de bienvenida
        welcome_label = QLabel(self)
        welcome_label.setText("Bienvenido al Launcher de Minecraft\nEste es un ejemplo de launcher.")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #ffffff;")

        # Botones con íconos
        start_button = self.create_button('Iniciar', 'assets/play.png', self.start_minecraft)
        exit_button = self.create_button('Salir', 'assets/exit.png', self.close)

        # Diseño de la interfaz con fondo oscuro
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # Márgenes más pequeños
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")  # Fondo oscuro y texto blanco

        layout.addWidget(welcome_label, alignment=Qt.AlignHCenter)
        layout.addStretch(1)  # Agrega un espacio elástico
        layout.addWidget(start_button, alignment=Qt.AlignHCenter)
        layout.addWidget(exit_button, alignment=Qt.AlignHCenter)
        layout.addStretch(1)  # Agrega un espacio elástico

    def create_button(self, text, icon_path, slot_function):
        button = QPushButton(text, self)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(32, 32))  # Ajusta el tamaño del ícono según sea necesario
        button.clicked.connect(slot_function)
        button.setStyleSheet(
            "QPushButton { background-color: #4c4c4c; color: #ffffff; border: 1px solid #555555; border-radius: 5px; }"
            "QPushButton:hover { background-color: #555555; }"
            "QPushButton:pressed { background-color: #333333; }"
        )
        return button

    def start_minecraft(self):
        # Aquí iría la lógica para iniciar Minecraft
        print('Iniciando Minecraft...')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    launcher = MinecraftLauncher()
    launcher.show()
    sys.exit(app.exec_())
