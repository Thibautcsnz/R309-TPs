import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDialog, QStackedWidget, QListWidget, QListWidgetItem, QMainWindow, QTextEdit, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor, QPalette, QColor, QLinearGradient
import hashlib
import socket
import mysql.connector
import threading

def get_gui_message():
    # Placeholder for the actual method to retrieve messages from the GUI
    # You should implement this method according to your PyQt application
    pass

class ClientThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, host, port, username, password, room):
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = username
        self.password = password
        self.room = room

    def run(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))

            # Send username first
            self.client_socket.send(self.username.encode())

            # Receive acknowledgement from the server (you can modify server code accordingly)
            ack = self.client_socket.recv(1024).decode()
            if ack != "ACK_USERNAME":
                print("Error: Server did not acknowledge the username.")
                return

            # Send password and room
            auth_data = f"{self.password};{self.room}"
            self.client_socket.send(auth_data.encode())

            # Start a separate thread to handle user input and send messages
            input_thread = threading.Thread(target=self.send_user_input)
            input_thread.start()

            while True:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                self.message_received.emit(message)
        except Exception as e:
            print(f"Error in ClientThread: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()

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
            print(f"Error sending user input: {e}")

    def send_message(self, message):
        if self.client_socket:
            self.client_socket.send(message.encode())
            print(f"Sent message: {message}")

class RoomWindow(QWidget):
    message_received = pyqtSignal(str)
    logout_requested = pyqtSignal()

    def __init__(self, username, client_thread, parent, user_manager):
        super().__init__()

        self.username = username
        self.client_thread = client_thread
        self.parent = parent
        self.user_manager = user_manager
        self.setWindowTitle(f"Interface de {username}")
        self.setGeometry(100, 100, 800, 600)
        self.room_list = QComboBox(self)
        self.init_ui()

    def init_ui(self):
        # Utilisez un QVBoxLayout pour organiser les widgets de haut en bas
        layout = QVBoxLayout()

        gradient_style = (
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, ""stop:0 #ADD8E6, stop:1 #B0C4DE);"  # Remplacez les codes couleur par ceux que vous souhaitez
        )
        self.setStyleSheet(gradient_style)

        # Titre du salon en haut à gauche
        self.title_label = QLabel("Bienvenue dans le salon général")
        layout.addWidget(self.title_label)

        # Statut de la personne en dessous
        label_status = QLabel('Statut: Connecté')
        layout.addWidget(label_status)

        # Liste des salons disponibles avec QComboBox
        self.room_list.addItem('Général')
        self.room_list.addItem('Blabla')
        self.room_list.addItem('Comptabilité')
        self.room_list.addItem('Informatique')
        self.room_list.addItem('Marketing')
        layout.addWidget(self.room_list)

        # Bouton de déconnexion
        logout_button = QPushButton('Déconnexion', self)
        layout.addWidget(logout_button)


        # Zone de texte pour envoyer le texte (ajustez la hauteur ici)
        self.message_edit = QTextEdit(self)
        self.message_edit.setFixedHeight(50)  # Ajustez la hauteur ici selon vos besoins
        layout.addWidget(self.message_edit)

        # Bouton pour envoyer le message
        send_button = QPushButton('Envoyer', self)
        layout.addWidget(send_button)

        # Zone de texte pour saisir le message
        self.input_edit = QLineEdit(self)
        layout.addWidget(self.input_edit)

        self.setLayout(layout)

        # Connectez le signal clicked du bouton à la méthode send_message
        send_button.clicked.connect(self.send_message)

        self.client_thread.message_received.connect(self.display_message)

        # Connecter le signal currentIndexChanged à la méthode room_changed
        self.room_list.currentIndexChanged.connect(self.room_changed)

        # Connectez le signal clicked du bouton de déconnexion à la méthode logout
        logout_button.clicked.connect(self.logout)

        # Connectez le signal clicked du bouton d'envoi à la fonction clear_message_input
        send_button.clicked.connect(self.clear_message_input)

    def clear_message_input(self):
        # Effacez le contenu de la zone de texte d'entrée
        self.input_edit.clear()

    def logout(self):
        # Émettez le signal de déconnexion
        self.logout_requested.emit()

    def room_changed(self, index):
        selected_room = self.room_list.currentText()
        self.update_title(selected_room)

        # Envoyer un message dans le salon sélectionné
        self.message_received.emit(f"@{self.username}: Change de salon vers {selected_room}")

        # Mettre à jour le statut de l'utilisateur dans la base de données
        self.user_manager.update_user_status(self.username, "connected" if selected_room else "disconnected")

    def display_message(self, message):
        # Afficher le message dans la zone de messagerie
        self.message_edit.append(message)

    def send_message(self):
        # Récupérer le message depuis la zone de texte de saisie
        message_text = self.input_edit.text()
        # Émettre le signal pour informer les autres parties de l'application
        self.message_received.emit(f"@{self.username}: {message_text}")

    def update_title(self, channel):
        self.title_label.setText(f"Bienvenue dans le salon {channel}")

class RegistrationWindow(QDialog):
    registration_successful_signal = pyqtSignal(str)

    def __init__(self, parent, user_manager):
        super().__init__()

        self.parent = parent
        self.user_manager = user_manager
        self.setWindowTitle("Inscription")
        self.setGeometry(200, 200, 400, 200)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

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

        self.register_button.clicked.connect(self.on_registration)
        self.back_button.clicked.connect(self.on_back)

        self.setLayout(layout)

    def on_registration(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if username and password:
            # Stocker le mot de passe en clair dans la base de données
            success = self.user_manager.register_user(username, password)
            if success:
                print("Inscription réussie!")
                self.registration_successful_signal.emit(username)
                self.accept()
            else:
                print("Le nom d'utilisateur existe déjà. Veuillez choisir un nom d'utilisateur différent.")
        else:
            print("Veuillez remplir tous les champs.")

    def on_back(self):
        self.parent.show_home_page()

class LoginWindow(QWidget):
    login_successful = pyqtSignal(str)
    login_failed = pyqtSignal()

    def __init__(self, parent, user_manager, host, port, room):
        super().__init__()

        self.parent = parent
        self.host = host
        self.port = port
        self.room = room
        self.user_manager = user_manager
        self.setWindowTitle("Connexion")
        self.setGeometry(200, 200, 400, 200)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

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

        # Champ de saisie pour l'adresse IP
        self.label_ip = QLabel('Adresse IP du serveur:')
        self.ip_input = QLineEdit(self)
        layout.addWidget(self.label_ip)
        layout.addWidget(self.ip_input)

        # Bouton pour définir l'adresse IP
        set_ip_button = QPushButton('Définir l\'adresse IP du serveur', self)
        layout.addWidget(set_ip_button)

        # Connectez le signal clicked du bouton à la méthode set_server_ip
        set_ip_button.clicked.connect(self.set_server_ip)

        self.login_button.clicked.connect(self.on_login)
        self.back_button.clicked.connect(self.on_back)

        self.setLayout(layout)

    def set_server_ip(self):
        new_ip = self.ip_input.text()
        if new_ip:
            self.parent.set_server_ip(new_ip)
            print(f"Adresse IP du serveur définie sur {new_ip}")
        else:
            print("Veuillez entrer une adresse IP valide.")

    def on_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Récupérer le mot de passe hashé stocké dans la base de données
        stored_password = self.user_manager.get_user_password(username)

        if stored_password:
            entered_hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Comparer le mot de passe entré avec celui stocké
            if entered_hashed_password == stored_password:
                print("Connexion Réussie !")
                self.login_successful.emit(username)
            else:
                print("Mot de passe incorrect.")
                self.login_failed.emit()
        else:
            print("Utilisateur non enregistré.")

    def on_back(self):
        self.parent.show_home_page()

class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()

        # Ajout de la fenêtre d'accueil
        self.home_page = HomePage(self)
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.addWidget(self.home_page)
        self.setCentralWidget(self.stacked_widget)

        # Initialiser le gestionnaire d'utilisateurs
        self.user_manager = UserManager()

        self.home_page.login_requested.connect(self.show_login_window)
        self.home_page.registration_requested.connect(self.show_registration_window)

        # Initialiser à la page d'accueil
        self.stacked_widget.setCurrentWidget(self.home_page)

        # Initialiser le thread client
        self.client_thread = None

        # Connectez le signal currentChanged pour détecter les changements de page
        self.stacked_widget.currentChanged.connect(self.page_changed)

        # Ajoutez ces lignes pour définir les attributs host, port, et room
        self.host = "127.0.0.1"
        self.port = 9000
        self.room = "Général"

        self.login_window = LoginWindow(self, self.user_manager, self.host, self.port, self.room)
        self.login_window.login_successful.connect(self.handle_login_successful)
        self.login_window.login_failed.connect(self.handle_login_failed)

    def set_server_ip(self, new_ip):
        self.host = new_ip
        self.dbhost = new_ip

    def show_registration_window(self):
        self.registration_window = RegistrationWindow(self, self.user_manager)
        self.registration_window.registration_successful_signal.connect(self.handle_registration_successful)
        self.stacked_widget.addWidget(self.registration_window)
        self.stacked_widget.setCurrentWidget(self.registration_window)

    def handle_registration_successful(self, username):
        print(f"Inscription réussie pour {username}")
        self.show_home_page()

    def show_login_window(self):
        self.login_window = LoginWindow(self, self.user_manager, host, port, room)
        self.login_window.login_successful.connect(self.handle_login_successful)
        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.setCurrentWidget(self.login_window)
        self.login_window.login_failed.connect(self.handle_login_failed)

    def handle_login_successful(self, username):
        print(f"Connexion réussie pour {username}")

        # Récupérer le mot de passe enregistré lors de l'inscription
        stored_password = self.user_manager.get_user_password(username)

        # Vérifier si l'utilisateur existe dans les utilisateurs enregistrés
        if stored_password:
            entered_password = self.login_window.password_input.text()
            entered_hashed_password = hashlib.sha256(entered_password.encode()).hexdigest()

            # Comparer le mot de passe entré avec celui enregistré
            if entered_hashed_password == stored_password:
                # Utiliser l'adresse IP spécifiée par l'utilisateur
                db_host = self.login_window.ip_input.text()
                client_thread = ClientThread(self.host, self.port, username, "", self.room)
                client_thread.start()
                self.set_client_thread(client_thread)
                self.show_room_window(username)
            else:
                print("Mot de passe incorrect.")
        else:
            print("Utilisateur non enregistré.")

    def handle_login_failed(self):
        print("Connexion échouée. Veuillez vérifier votre nom d'utilisateur ou votre mot de passe")

    def show_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)

    def show_room_window(self, username, channel="Général"):
        self.room_window = RoomWindow(username, self.client_thread, self, self.user_manager)
        self.stacked_widget.addWidget(self.room_window)
        self.stacked_widget.setCurrentWidget(self.room_window)
        self.room_window.message_received.connect(self.send_message_to_server)

        # Connectez le signal currentIndexChanged de room_list à handle_room_change
        self.room_window.room_list.currentIndexChanged.connect(self.handle_room_change)

        # Connectez le signal logout_requested de RoomWindow à handle_logout_requested
        self.room_window.logout_requested.connect(self.handle_logout_requested)

        # Mettre à jour le titre et envoyer un message pour le salon initial
        self.room_window.update_title(channel)
        self.client_thread.send_message(f"@{username}: Rejoint le salon {channel}")

    def handle_logout_requested(self):
        # Gérez la déconnexion ici
        self.client_thread.send_message(f"@{self.room_window.username}: Quitte le salon")
        self.client_thread.terminate()  # Terminez le thread client
        self.client_thread.wait()  # Attendez que le thread client se termine
        self.show_home_page()

    # Ajouter la méthode handle_room_change pour gérer les changements de salon
    def handle_room_change(self, index):
        selected_room = self.room_window.room_list.currentText()
        self.room_window.update_title(selected_room)
        self.client_thread.send_message(f"@{self.room_window.username}: Change de salon vers {selected_room}")

    def registration_successful(self, username):
        # Effectuer toute action nécessaire après une inscription réussie
        # Dans cet exemple, nous allons simplement montrer la page des messages
        self.stacked_widget.setCurrentWidget(self.home_page)  # Ajout de cette ligne pour revenir à la page d'accueil
        self.show_room_window(username, "Général")  # Mettez le canal initial ici

    def page_changed(self, index):
        # Cette méthode est appelée lorsque la page actuelle change
        # Vous pouvez ajouter du code supplémentaire ici si nécessaire
        pass

    def send_message_to_server(self, message):
        try:
            if self.client_thread:
                self.client_thread.send_message(message)
                print(f"Message envoyé au serveur : {message}")
            else:
                print("Erreur: Thread client non initialisé.")
        except Exception as e:
            print(f"Erreur lors de l'envoi du message au serveur : {e}")

    def set_client_thread(self, client_thread):
        self.client_thread = client_thread

class HomePage(QWidget):
    registration_requested = pyqtSignal()
    login_requested = pyqtSignal()

    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.setWindowTitle("Connexion / Inscription à l'application de messagerie")
        self.setGeometry(300, 200, 400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.login_button = QPushButton('Connexion', self)
        self.login_button.setStyleSheet("background-color: #FFB900; color: white;")
        self.register_button = QPushButton('Inscription', self)
        self.register_button.setStyleSheet("background-color: #FFB900; color: white;")

        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.login_button.clicked.connect(self.on_login_clicked)
        self.register_button.clicked.connect(self.on_register_clicked)

        self.setLayout(layout)

    def on_login_clicked(self):
        self.login_requested.emit()

    def on_register_clicked(self):
        self.registration_requested.emit()

class UserManager:
    def __init__(self):
        # Établir une connexion à la base de données
        self.connection = mysql.connector.connect(
            host="127.0.0.1",
            user="serv302",
            password="serv2024",
            database="sae302"
        )
        if self.connection.is_connected():
            print(f"Connexion à la base de donnée en {host}")
        else:
            print("Erreur de connexion à la base de donnée")

        self.cursor = self.connection.cursor()

        # Créer la table si elle n'existe pas
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

    def get_user_password(self, username):
        # Récupérer le mot de passe de l'utilisateur depuis la base de données
        self.cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        result = self.cursor.fetchone()

        if result:
            return result[0]  # Retourne le mot de passe
        else:
            return None  # Aucun utilisateur trouvé

    def register_user(self, username, password):
        # Vérifier si l'utilisateur existe déjà
        self.cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        if self.cursor.fetchone():
            return False  # L'utilisateur existe déjà

        # Hasher le mot de passe
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Insérer l'utilisateur dans la base de données avec le mot de passe hashé
        self.cursor.execute("INSERT INTO user (username, password, alias) VALUES (%s, %s, %s)",
                            (username, hashed_password, 'DefaultAlias'))
        self.connection.commit()
        return True  # Inscription réussie

    def check_credentials(self, username, entered_password):
        # Vérifier les informations d'identification dans la base de données
        self.cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, entered_password))
        return bool(self.cursor.fetchone())

    def update_user_status(self, username, status):
        # Vérifier si l'utilisateur existe
        if self.get_user_password(username) is not None:
            # Mettre à jour le statut de l'utilisateur dans la base de données
            self.cursor.execute("UPDATE user SET status = %s WHERE username = %s", (status, username))
            self.connection.commit()
        else:
            print(f"Utilisateur {username} non trouvé. Impossible de mettre à jour le statut.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Messagerie")
    # Ajouter les détails du serveur
    host = "127.0.0.1"
    port = 9000  # Remplacez 1234 par le port de votre serveur
    room = "Général"  # Remplacez "General" par le salon par défaut
    client = ChatClient()
    client.show()
    sys.exit(app.exec())