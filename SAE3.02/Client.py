"""
Application de messagerie (côté client)

Cette application met en œuvre un client de chat utilisant PyQt6 pour l'interface utilisateur graphique (GUI) et des sockets pour la communication avec un serveur de chat.
Le client permet aux utilisateurs de s'inscrire, de se connecter, de rejoindre différents salons de discussion et d'envoyer des messages à d'autres utilisateurs en temps réel.

Classes:
    - ClientThread: classe basée sur QThread chargée de gérer la communication entre le client et le serveur.
    - RoomWindow: La fenêtre principale représentant l'espace de discussion où les utilisateurs peuvent interagir.
    - RegistrationWindow: gère l'inscription des utilisateurs.
    - LoginWindow: gère les fonctions de connexion des utilisateurs.
    - ChatClient: La fenêtre principale de l'application qui contrôle l'ensemble du processus.

Utilisation :
    1. Lancer l'application.
    2. Définissez l'adresse IP du serveur sur la page d'accueil.
    3. Connectez-vous ou créez un nouveau compte utilisateur.
    4. Rejoignez un salon de discussion et commencez à interagir avec d'autres utilisateurs.

Author:
    COSENZA Thibaut

Date:
    31/12/2023
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialog, QStackedWidget, QListWidget, QInputDialog, QListWidgetItem, QMainWindow, QTextEdit, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor, QPalette, QColor, QLinearGradient
import hashlib
import socket
import mysql.connector
import threading

    # Fonction factice qui peut être remplacée par la fonction réelle gérant les messages de l'interface utilisateur.
def get_gui_message():
    pass

class ClientThread(QThread):
    message_received = pyqtSignal(str)
    """
        Thread responsable de la gestion de la communication côté client avec le serveur.
    """
    def __init__(self, host, port, username, password, room):

        """
            Initialise ClientThread avec les paramètres fournis.
            Paramètres :
            - host (str) : Adresse de l'hôte du serveur.
            - port (int) : Numéro de port du serveur.
            - username (str) : Nom d'utilisateur choisi par l'utilisateur.
            - password (str) : Mot de passe de l'utilisateur.
            - room (str) : Channel initial de l'utilisateur.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = username
        self.password = password
        self.room = room

    def run(self):

        """
            Méthode principale du thread, responsable de la connexion au serveur,
            de l'authentification de l'utilisateur et de la réception continue des messages du serveur.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.send(self.username.encode())

            # Reçois l'accusé de réception du serveur.
            ack = self.client_socket.recv(1024).decode()
            if ack != "ACK_USERNAME":
                print("Erreur : Le serveur n'a pas reconnu le nom d'utilisateur.")
                return

            # Envoie le mot de passe et le channel.
            auth_data = f"{self.password};{self.room}"
            self.client_socket.send(auth_data.encode())

            # Démarrer un thread séparé pour gérer les entrées de l'utilisateur et envoyer des messages.
            input_thread = threading.Thread(target=self.send_user_input)
            input_thread.start()

            while True:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                self.message_received.emit(message)
        except Exception as e:
            print(f"Erreur dans le thread client : {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()

    # Méthode pour envoyer les messages saisis par l'utilisateur au serveur.
    def send_user_input(self):
        try:
            while True:
                message = yield from get_gui_message()
                if not message:
                    break
                full_message = f"{self.username}: {message}"
                # Envoyer le message au serveur pour la diffusion
                self.client_socket.send(full_message.encode())
        except Exception as e:
            print(f"Erreur lors de l'envoi des données de l'utilisateur : {e}")

    # Méthode pour récupérer le message depuis la zone de texte de saisie et l'envoyer au serveur.
    def send_message(self, message):
        if self.client_socket:
            self.client_socket.send(message.encode())
            print(f"Message envoyé: {message}")

class RoomWindow(QWidget):
    """
        Représente la fenêtre principale dans laquelle les utilisateurs interagissent avec l'espace de discussion.
    """
    message_received = pyqtSignal(str)
    logout_requested = pyqtSignal()

    def __init__(self, username, client_thread, parent, user_manager):
        """
            Initialise la fenêtre RoomWindow avec les paramètres fournis.

            Paramètres :
            - nom d'utilisateur (str) : Nom d'utilisateur de l'utilisateur.
            - client_thread (ClientThread) : Le thread du client qui gère la communication.
            - parent : Le widget parent.
            - user_manager : Instance du gestionnaire d'utilisateurs.
        """
        super().__init__()

        self.username = username
        self.client_thread = client_thread
        self.parent = parent
        self.user_manager = user_manager
        self.setWindowTitle(f"Interface de {username}")
        self.setMinimumSize(300, 250)
        self.room_list = QComboBox(self)
        self.init_ui()

    # Initialise l'interface utilisateur de la fenêtre principale.
    def init_ui(self):
        # Utilisation d'un QVBoxLayout pour organiser les widgets de haut en bas.
        layout = QVBoxLayout()

        # Définition de la couleur.
        gradient_style = (
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, ""stop:0 #ADD8E6, stop:1 #B0C4DE);"
        )
        self.setStyleSheet(gradient_style)

        # Titre du salon.
        self.title_label = QLabel("Bienvenue dans le salon général")
        layout.addWidget(self.title_label)

        # Statut de la personne sur l'application.
        label_status = QLabel('Statut: Connecté')
        layout.addWidget(label_status)

        # Liste des salons disponibles avec QComboBox.
        self.room_list.addItem('Général')
        self.room_list.addItem('Blabla')
        self.room_list.addItem('Comptabilité')
        self.room_list.addItem('Informatique')
        self.room_list.addItem('Marketing')
        layout.addWidget(self.room_list)

        # Bouton de déconnexion.
        logout_button = QPushButton('Déconnexion', self)
        layout.addWidget(logout_button)

        # Zone de texte pour envoyer le texte.
        self.message_edit = QTextEdit(self)
        self.message_edit.setFixedHeight(90)
        layout.addWidget(self.message_edit)

        # Bouton pour envoyer le message.
        send_button = QPushButton('Envoyer', self)
        layout.addWidget(send_button)

        # Zone de texte pour saisir le message.
        self.input_edit = QLineEdit(self)
        layout.addWidget(self.input_edit)

        self.setLayout(layout)

        # Connexion du signal "bouton clické" du bouton d'envoi à la méthode "send_message".
        send_button.clicked.connect(self.send_message)

        self.client_thread.message_received.connect(self.display_message)

        # Connexion du signal "currentIndexChanged" à la méthode "room_changed".
        self.room_list.currentIndexChanged.connect(self.room_changed)

        # Connexion du signal "bouton clické" du bouton de déconnexion à la méthode "logout".
        logout_button.clicked.connect(self.logout)

        # Connexion du signal "bouton clické" du bouton d'envoi à la fonction "clear_message_input".
        send_button.clicked.connect(self.clear_message_input)

    # Fonction effaçant le contenu de la zone de texte d'entrée.
    def clear_message_input(self):
        self.input_edit.clear()

    # Fonction émettant le signal de déconnexion.
    def logout(self):
        self.logout_requested.emit()

    # Fonction gérant le changement de salon.
    def room_changed(self, index):
        selected_room = self.room_list.currentText()
        self.update_title(selected_room)
        # Envoie un message dans le salon sélectionné.
        self.message_received.emit(f"@{self.username}: Change de salon vers {selected_room}")
        # Met à jour le statut de l'utilisateur dans la base de données.
        self.user_manager.update_user_status(self.username, "connected" if selected_room else "disconnected")

    # Fonction affichant le message dans la zone de texte principale.
    def display_message(self, message):
        self.message_edit.append(message)

    # Fonction récupèrant le message depuis la zone de texte de saisie et envoie au serveur.
    def send_message(self):
        message_text = self.input_edit.text()
        # Émet le signal pour informer les autres parties de l'application.
        self.message_received.emit(f"@{self.username}: {message_text}")

    # Fonction mettant à jour le titre avec le nom du channel sélectionné.
    def update_title(self, channel):
        self.title_label.setText(f"Bienvenue dans le salon {channel}")

class RegistrationWindow(QDialog):
    """
        Représente la fenêtre d'enregistrement pour les nouveaux utilisateurs.
    """
    registration_successful_signal = pyqtSignal(str)

    def __init__(self, parent, user_manager):
        """
            Initialise la fenêtre d'enregistrement avec les paramètres fournis.

            Paramètres :
            - parent : Le widget parent.
            - user_manager : Instance du gestionnaire d'utilisateurs.
        """
        super().__init__()

        self.parent = parent
        self.user_manager = user_manager
        self.setWindowTitle("Inscription")
        self.setGeometry(200, 200, 400, 200)

        self.init_ui()

    # Initialise l'interface utilisateur de la fenêtre d'enregistrement.
    def init_ui(self):
        layout = QVBoxLayout()

        # Déclaration des différents boutons et widgets pour la fenêtre d'inscription.
        self.label_username = QLabel('Nom (pseudonyme):')
        self.username_input = QLineEdit(self)
        self.label_password = QLabel('Mot de passe:')
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Masque le texte entré
        self.register_button = QPushButton('Inscription', self)
        self.register_button.setStyleSheet("background-color: #3498DB; color: white;")
        self.back_button = QPushButton('Retour', self)

        layout.addWidget(self.label_username)
        layout.addWidget(self.username_input)
        layout.addWidget(self.label_password)
        layout.addWidget(self.password_input)
        layout.addWidget(self.register_button)
        layout.addWidget(self.back_button)

        # Connexion des boutons "inscription" et "retour" au différentes méthodes
        self.register_button.clicked.connect(self.on_registration)
        self.back_button.clicked.connect(self.on_back)

        self.setLayout(layout)

    # Fonction gérant le processus d'enregistrement de l'utilisateur.
    def on_registration(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if username and password:
            # Stocke le mot de passe en clair dans la base de données.
            success = self.user_manager.register_user(username, password)
            if success:
                print("Inscription réussie!")
                self.registration_successful_signal.emit(username)
                self.accept()
            else:
                print("Le nom d'utilisateur existe déjà. Veuillez choisir un nom d'utilisateur différent.")
        else:
            print("Veuillez remplir tous les champs.")

    # Fonction gèrant le retour à la page précédente.
    def on_back(self):
        self.parent.show_home_page()

class LoginWindow(QWidget):
    """
        Représente la fenêtre de connexion pour les utilisateurs existants.
    """
    login_successful = pyqtSignal(str)
    login_failed = pyqtSignal()

    def __init__(self, parent, user_manager, host, port, room):
        """
            Initialise la fenêtre de connexion avec les paramètres fournis.

            Paramètres :
            - parent : Le widget parent.
            - user_manager : Instance du gestionnaire d'utilisateurs.
            - host (str) : Adresse de l'hôte du serveur.
            - port (int) : Numéro de port du serveur.
            - room (str) : Channel initial pour l'utilisateur.
        """
        super().__init__()

        self.parent = parent
        self.host = host
        self.port = port
        self.room = room
        self.user_manager = user_manager
        self.setWindowTitle("Connexion")
        self.setGeometry(200, 200, 400, 200)
        self.init_ui()

    # Initialise l'interface utilisateur de la fenêtre de connexion.
    def init_ui(self):
        layout = QVBoxLayout()

        # Déclaration des différents boutons et widgets pour la fenêtre de connexion
        self.label_username = QLabel('Nom (pseudonyme):')
        self.username_input = QLineEdit(self)
        self.label_password = QLabel('Mot de passe:')
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Masque le texte entré
        self.login_button = QPushButton('Connexion', self)
        self.login_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.back_button = QPushButton('Retour', self)

        layout.addWidget(self.label_username)
        layout.addWidget(self.username_input)
        layout.addWidget(self.label_password)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.back_button)

        self.login_button.clicked.connect(self.on_login)
        self.back_button.clicked.connect(self.on_back)

        self.setLayout(layout)

    # Méthode pour définir l'adresse IP du serveur.
    def set_server_ip(self):
        new_ip = self.ip_input.text()
        if new_ip:
            self.parent.set_server_ip(new_ip)
            print(f"Adresse IP du serveur définie sur {new_ip}")
        else:
            print("Veuillez entrer une adresse IP valide.")

    # Fonction gérant le processus de connexion de l'utilisateur.
    def on_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Récupère le mot de passe "hashé" stocké dans la base de données.
        stored_password = self.user_manager.get_user_password(username)

        if stored_password:
            entered_hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Compare le mot de passe entré avec celui stocké dans la base de données.
            if entered_hashed_password == stored_password:
                print("Connexion Réussie !")
                self.login_successful.emit(username)
            else:
                print("Mot de passe incorrect.")
                self.login_failed.emit()
        else:
            print("Utilisateur non enregistré.")

    # Fonction gérant le retour à la page précédente.
    def on_back(self):
        self.parent.show_home_page()

class ChatClient(QMainWindow):
    """
        Fenêtre principale de l'application qui gère les différentes pages et les interactions avec l'utilisateur.
    """
    def __init__(self):
        """
            Initialise l'application ChatClient.
        """
        super().__init__()

        # Définition des widgets pour la fenêtre d'accueil.
        self.home_page = HomePage(self)
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.addWidget(self.home_page)
        self.setCentralWidget(self.stacked_widget)

        # Définition des attributs host, port, et room.
        self.host = host
        self.port = 9000
        self.room = "Général"

        # Initialise le gestionnaire d'utilisateurs
        self.user_manager = UserManager()

        self.home_page.login_requested.connect(self.show_login_window)
        self.home_page.registration_requested.connect(self.show_registration_window)

        # Initialise la page d'accueil
        self.stacked_widget.setCurrentWidget(self.home_page)

        # Initialise le thread client
        self.client_thread = None

        # Connexion du signal "currentChanged" pour détecter les changements de pages.
        self.stacked_widget.currentChanged.connect(self.page_changed)

        self.login_window = LoginWindow(self, self.user_manager, self.host, self.port, self.room)
        self.login_window.login_successful.connect(self.handle_login_successful)
        self.login_window.login_failed.connect(self.handle_login_failed)
        self.login_window.set_server_ip = lambda new_ip: self.set_server_ip(new_ip)

        # Connexion du signal "set_ip_requested" de la classe "Homepage" à la méthode "set_server_ip".
        self.home_page.set_ip_requested.connect(self.user_manager.set_db_host)

    # Fonction définissant l'adresse IP du serveur.
    def set_server_ip(self, new_ip):
        self.host = new_ip
        self.dbhost = new_ip

    # Fonction affichant la fenêtre d'enregistrement.
    def show_registration_window(self):
        self.registration_window = RegistrationWindow(self, self.user_manager)
        self.registration_window.registration_successful_signal.connect(self.handle_registration_successful)
        self.stacked_widget.addWidget(self.registration_window)
        self.stacked_widget.setCurrentWidget(self.registration_window)

    # Fonction gérant les actions après une inscription réussie.
    def handle_registration_successful(self, username):
        print(f"Inscription réussie pour {username}")
        self.show_home_page()

    # Fonction affichant la fenêtre de connexion.
    def show_login_window(self):
        self.login_window = LoginWindow(self, self.user_manager, host, port, room)
        self.login_window.login_successful.connect(self.handle_login_successful)
        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.setCurrentWidget(self.login_window)
        self.login_window.login_failed.connect(self.handle_login_failed)

    # Fonction gérant les actions après une connexion réussie.
    def handle_login_successful(self, username):
        print(f"Connexion réussie pour {username}")

        # Récupère le mot de passe enregistré lors de l'inscription.
        stored_password = self.user_manager.get_user_password(username)

        # Vérifie si l'utilisateur existe dans les utilisateurs enregistrés.
        if stored_password:
            entered_password = self.login_window.password_input.text()
            entered_hashed_password = hashlib.sha256(entered_password.encode()).hexdigest()

            # Compare le mot de passe entré avec celui enregistré.
            if entered_hashed_password == stored_password:
                # Utilise l'adresse IP spécifiée par l'utilisateur.
                client_thread = ClientThread(self.host, self.port, username, "", self.room)
                client_thread.start()
                self.set_client_thread(client_thread)
                self.show_room_window(username)
            else:
                print("Mot de passe incorrect.")
        else:
            print("Utilisateur non enregistré.")

    # Fonction gérant les actions après une connexion échouée.
    def handle_login_failed(self):
        print("Connexion échouée. Veuillez vérifier votre nom d'utilisateur ou votre mot de passe")

    # Fonction affichant la page d'accueil.
    def show_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.stacked_widget.addWidget(self.login_window)

    # Fonction affichant la fenêtre principale de la discussion.
    def show_room_window(self, username, channel="Général"):
        self.room_window = RoomWindow(username, self.client_thread, self, self.user_manager)
        self.stacked_widget.addWidget(self.room_window)
        self.stacked_widget.setCurrentWidget(self.room_window)
        self.room_window.message_received.connect(self.send_message_to_server)

        # Connexion du signal "currentIndexChanged" de "room_list" à "handle_room_change".
        self.room_window.room_list.currentIndexChanged.connect(self.handle_room_change)

        # Connexion du signal "logout_requested" de "RoomWindow" à "handle_logout_requested".
        self.room_window.logout_requested.connect(self.handle_logout_requested)

        # Met à jour le titre et envoie un message pour le salon initial.
        self.room_window.update_title(channel)
        self.client_thread.send_message(f"@{username}: Rejoint le salon {channel}")

    # Fonction gérant la déconnexion de l'utilisateur.
    def handle_logout_requested(self):
        self.client_thread.send_message(f"@{self.room_window.username}: Quitte le salon")
        self.client_thread.terminate()
        self.client_thread.wait()
        self.show_home_page()

    # Méthode gérant les changements de salon.
    def handle_room_change(self, index):
        selected_room = self.room_window.room_list.currentText()
        self.room_window.update_title(selected_room)
        self.client_thread.send_message(f"@{self.room_window.username}: Change de salon vers {selected_room}")

    # Fonction effectuant des actions après une inscription réussie.
    def registration_successful(self, username):
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.show_room_window(username, "Général")

    # Méthode appelée lorsque la page actuelle change.
    def page_changed(self, index):
        pass

    # Fonction envoyant un message au serveur.
    def send_message_to_server(self, message):
        try:
            if self.client_thread:
                self.client_thread.send_message(message)
                print(f"Message envoyé au serveur : {message}")
            else:
                print("Erreur: Thread client non initialisé.")
        except Exception as e:
            print(f"Erreur lors de l'envoi du message au serveur : {e}")

    # Fonction définissant le thread client.
    def set_client_thread(self, client_thread):
        self.client_thread = client_thread

class HomePage(QWidget):
    """
        Représente la page d'accueil de l'application où les utilisateurs peuvent se connecter ou s'enregistrer.
    """
    registration_requested = pyqtSignal()
    login_requested = pyqtSignal()
    set_ip_requested = pyqtSignal(str)

    def __init__(self, parent):
        """
            Initialise la page d'accueil avec les paramètres fournis.

            Paramètres :
            - parent : Le widget parent.
        """
        super().__init__()

        self.parent = parent
        self.setWindowTitle("Connexion / Inscription à l'application de messagerie")
        self.setGeometry(300, 200, 400, 200)
        self.init_ui()

    # Initialise l'interface utilisateur de la page d'accueil.
    def init_ui(self):
        layout = QVBoxLayout()

        # Définition des boutons.
        self.login_button = QPushButton('Connexion', self)
        self.login_button.setStyleSheet("background-color: #FFB900; color: white;")
        self.register_button = QPushButton('Inscription', self)
        self.register_button.setStyleSheet("background-color: #FFB900; color: white;")

        # Champ texte et bouton pour définir l'adresse IP.
        self.label_ip = QLabel('Adresse IP du serveur:')
        self.ip_input = QLineEdit(self)
        layout.addWidget(self.label_ip)
        layout.addWidget(self.ip_input)
        set_ip_button = QPushButton('Définir l\'adresse IP du serveur', self)
        layout.addWidget(set_ip_button)

        # Connexion du signal "bouton clické" à la méthode "set_db_host" de UserManager.
        set_ip_button.clicked.connect(self.set_db_host)

        # Ajout des boutons "Connexion" et "Inscription".
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.login_button.clicked.connect(self.on_login_clicked)
        self.register_button.clicked.connect(self.on_register_clicked)

        self.setLayout(layout)

    # Méthode pour définir l'adresse IP du serveur.
    def set_db_host(self):
        new_ip = self.ip_input.text()
        if new_ip:
            self.set_ip_requested.emit(new_ip)
            print(f"Adresse IP du serveur définie sur {new_ip}")
        else:
            print("Veuillez entrer une adresse IP valide.")

    # Fonction émettant le signal de demande de connexion.
    def on_login_clicked(self):
        self.login_requested.emit()

    # Fonction émettant le signal de demande d'enregistrement.
    def on_register_clicked(self):
        self.registration_requested.emit()

    # Méthode pour définir l'adresse IP du serveur.
    def set_server_ip(self):
        new_ip = self.ip_input.text()
        if new_ip:
            self.set_ip_requested.emit(new_ip)
            print(f"Adresse IP du serveur définie sur {new_ip}")
        else:
            print("Veuillez entrer une adresse IP valide.")

class UserManager:
    """
        Gère les opérations liées à l'utilisateur telles que l'enregistrement, la connexion et l'interaction avec la base de données.
    """
    def __init__(self):
        """
            Initialise le gestionnaire d'utilisateurs (UserManager).
        """
        self.connection = None
        self.cursor = None

    # Fonction établissant la connexion à la base de données avec l'adresse IP fournie.
    def set_db_host(self, host):
        self.connection = mysql.connector.connect(
                host=host,
                user="serv302",
                password="serv2024",
                database="sae302"
            )

        if self.connection.is_connected():
            print(f"Connexion à la base de données en {host}")
            self.cursor = self.connection.cursor()
            self.create_table_if_not_exists()
        else:
            print("Erreur de connexion à la base de données")

        self.cursor = self.connection.cursor()

    # Fonction créeant la table "user" si elle n'existe pas.
    def create_table_if_not_exists(self):
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                alias VARCHAR(255) DEFAULT 'DefaultAlias',
                status ENUM('connected', 'disconnected', 'absent') DEFAULT 'disconnected'
            )
        """)
            self.connection.commit()

    # Fonction récupérant le mot de passe de l'utilisateur depuis la base de données.
    def get_user_password(self, username):
        # Récupère le mot de passe de l'utilisateur depuis la base de données.
        self.cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        result = self.cursor.fetchone()

        if result:
            return result[0]
        else:
            return None

    # Fonction enregistrant un nouvel utilisateur dans la base de données.
    def register_user(self, username, password):
        # Vérifie si l'utilisateur existe déjà.
        self.cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        if self.cursor.fetchone():
            return False
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Insère l'utilisateur dans la base de données avec le mot de passe hashé.
        self.cursor.execute("INSERT INTO user (username, password, alias) VALUES (%s, %s, %s)",
                            (username, hashed_password, 'DefaultAlias'))
        self.connection.commit()
        return True

    # Fonction vérifiant les informations d'identification dans la base de données.
    def check_credentials(self, username, entered_password):
        # Vérifie les informations d'identification dans la base de données.
        self.cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, entered_password))
        return bool(self.cursor.fetchone())

    # Fonction mettant à jour le statut de l'utilisateur dans la base de données.
    def update_user_status(self, username, status):
        # Vérifie si l'utilisateur existe.
        if self.get_user_password(username) is not None:
            # Met à jour le statut de l'utilisateur dans la base de données.
            self.cursor.execute("UPDATE user SET status = %s WHERE username = %s", (status, username))
            self.connection.commit()
        else:
            print(f"Utilisateur {username} non trouvé. Impossible de mettre à jour le statut.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Application FASTCHAT")
    # Ajout des détails du serveur
    host = "127.0.0.1"
    port = 9000
    room = "Général"
    client = ChatClient()
    client.show()
    sys.exit(app.exec())