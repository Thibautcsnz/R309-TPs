# Partie3 : interface graphique (Bouton Stop)
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QComboBox, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QGridLayout
import sys
import threading
import time

class Chronomètre(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.label_instruction = QLabel("Compteur :")
        self.entry = QLineEdit()
        self.label_result = QLabel()
        self.setGeometry(50, 500, 200, 200)
        self.valeur = 0
        self.texte_label = QLabel(str(self.valeur))

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.__start)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect
        self.quitter_button = QPushButton("Quitter")
        self.quitter_button.clicked.connect(self.close)

        # Mise en page
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.label_instruction)
        input_layout.addWidget(self.entry)

        result_layout = QVBoxLayout()
        result_layout.addWidget(self.label_result)

        button_layout = QGridLayout()
        button_layout.addWidget(self.start_button, 1, 1)
        button_layout.addWidget(self.reset_button, )
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.quitter_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addLayout(result_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Chronomètre")


    def start(__start):
        self.valeur += 1
        while reset(self)==False:
            self.valeur += 1
            texte=(f"{self.valeur}")
        if not self.chronometre_thread.isRunning():
            self.chronometre_thread.start()

        update_signal = pyqtSignal(int)

    def __start():
        valeur = 0
        while True:
            self.update_signal.emit(valeur)
            valeur += 1
            time.sleep(1)
        self.arret_thread = False
        if not self.chronometre_thread.isRunning():
            self.chronometre_thread.start()

    def reset(self):
        texte = self.valeur

    def stop(self):
        self.arret_thread = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chrono = Chronomètre()
    chrono.show()
    sys.exit(app.exec())