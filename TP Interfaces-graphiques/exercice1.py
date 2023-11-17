import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton

class MaApplication(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Une première fenêtre")
        self.setGeometry(100, 100, 400, 200)
        self.button_ok = QPushButton("Ok")
        self.button_ok.clicked.connect(self.on_button_ok_click)
        self.result_label = QLabel("")
        # Widget QLabel pour afficher du texte statique
        label = QLabel("Saisir votre nom")
        self.button_quit = QPushButton("Quitter")
        self.button_quit.clicked.connect(self.close)

        # Widget QLineEdit pour une zone de texte modifiable
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("")

        # Créer une disposition verticale
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_ok)
        layout.addWidget(self.result_label)
        layout.addWidget(self.button_quit)

        # Appliquer la disposition à la fenêtre principale
        self.setLayout(layout)

    def on_button_ok_click(self):
        texte_saisi = self.text_edit.text()
        self.result_label.setText(f"Bonjour {texte_saisi}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    fenetre = MaApplication()
    fenetre.show()
    sys.exit(app.exec())
