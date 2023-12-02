# Partie5 : interface graphique (Bouton Connect)
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
import sys
import time
import threading
import socket

class ChronometreThread(threading.Thread):
    update_signal = pyqtSignal(int)
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.client_socket = None

    def run(self):
        compteur = 0
        while not self.parent.arret_thread:
            compteur += 1
            self.update_signal.emit(compteur)
            if self.client_socket:
                self.client_socket.send(f"Compteur : {compteur}".encode())
            time.sleep(1)

class Chronometre(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.label_instruction = QLabel("Compteur :")
        self.entry = QLineEdit()
        self.label_result = QLabel()
        self.valeur = 0
        self.texte_label = QLabel(str(self.valeur))
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.__start)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect)
        self.quitter_button = QPushButton("Quitter")
        self.quitter_button.clicked.connect(self.quitter)

        self.arret_thread = False
        self.client_socket = None
        self.chronometre_thread = ChronometreThread(parent=self)
        self.chronometre_thread.update_signal.connect(self.update_text)

        # Mise en page
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.label_instruction)
        input_layout.addWidget(self.entry)

        result_layout = QVBoxLayout()
        result_layout.addWidget(self.label_result)

        button_layout = QGridLayout()
        button_layout.addWidget(self.start_button, 1, 1)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.quitter_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addLayout(result_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Chronomètre")

    def __start(self):
        self.arret_thread = False
        if not self.chronometre_thread.is_alive():
            self.chronometre_thread.start()

    def reset(self):
        self.valeur = 0
        self.texte_label.setText(str(self.valeur))
        if self.client_socket:
            self.client_socket.send("Reset".encode())
        self.arret_thread = True

    def stop(self):
        self.arret_thread = True
        if self.client_socket:
            self.client_socket.send("Stop".encode())

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("localhost", 10000))
            QMessageBox.information(self, "Connexion réussie", "Connexion au serveur réussie.")
        except Exception as e:
            QMessageBox.warning(self, "Erreur de connexion", f"Erreur de connexion au serveur : {str(e)}")

    def quitter(self):
        self.stop()
        if self.client_socket:
            self.client_socket.send("bye".encode())
            self.client_socket.close()
        QApplication.exit(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chrono = Chronometre()
    chrono.show()
    sys.exit(app.exec())