"""
Serveur de chat multi-utilisateur avec interface graphique PyQt.

Le serveur gère les connexions des clients, la diffusion des messages entre les utilisateurs connectés,
l'authentification des utilisateurs administrateurs, le kick / ban d'utilisateurs, et l'arrêt du serveur.

Classes :
- AuthDialog : Fenêtre de dialogue pour l'authentification des administrateurs.
- UserSignal : Classe pour la mise à jour des utilisateurs connectés.
- UserManager : Gestionnaire des utilisateurs : messages et actions administratives.
- ServerThread : Thread principal du serveur qui accepte les connexions des clients et les gère.
- ServerGUI : Interface graphique pour l'administration du serveur.
- ClientHandler : Gestionnaire de messages pour chaque client connecté.

Le code utilise PyQt6 pour l'interface graphique et le multithreading pour gérer les connexions des clients
de manière asynchrone. Il utilise également une base de données MySQL pour stocker les messages
et les utilisateurs bannis.

Note : Assurez-vous d'installer PyQt6 et le module MySQL Connector avant d'exécuter le code.

Utilisation :
    1. Lancer l'application.
    2. Connectez-vous avec l'identifiant et le mot de passe donné.
    3. Administrez votre application de messagerie

Author:
    COSENZA Thibaut

Date:
    31/12/2023
"""

import sys
import socket
import threading
import time
import queue
import mysql.connector
from functools import partial
from PyQt6.QtGui import QPalette, QColor, QLinearGradient
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QDialog, QLabel, QLineEdit, QDialog, QMessageBox

class AuthDialog(QDialog):
    """
        Fenêtre de dialogue pour l'authentification des administrateurs.
    """
    def __init__(self):
        """
        Initialise la fenêtre de dialogue et ses composants.
        """
        super().__init__()

        self.setWindowTitle("Authentification du serveur")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()
        # QLabel et QlineEdit pour le champs de saisie du nom d'utilisateur.
        self.username_label = QLabel("Nom d'utilisateur:")
        self.username_input = QLineEdit(self)

        # QLabel et QlineEdit pour le champs de saisie du mot de passe administrateur.
        self.password_label = QLabel("Mot de passe:")
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # QPushButton pour déclencher le processus d'authentification.
        self.login_button = QPushButton("Connexion", self)
        self.login_button.clicked.connect(self.authenticate)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    # Méthode appelée lorsqu'un utilisateur tente de s'authentifier.
    def authenticate(self):
        # Nom d'utilisateur et mot de passe à utiliser pour l'administrateur.
        correct_username = "admin"
        correct_password = "serv2024!"

        # Récupère le nom d'utilisateur et le mot de passe saisis.
        entered_username = self.username_input.text()
        entered_password = self.password_input.text()

        # Vérifie si les informations d'authentification sont correctes.
        if entered_username == correct_username and entered_password == correct_password:
            self.accept()
        else:
            QMessageBox.warning(self, "Authentification échouée", "Nom d'utilisateur ou mot de passe incorrect.")


class UserSignal(QObject):
    """
        Classe pour la mise à jour des utilisateurs connectés.
         - user_updated: Signal émis lorsqu'un utilisateur est ajouté, supprimé, ou lorsqu'il y a des mises à jour.
    """
    user_updated = pyqtSignal()

class UserManager:
    """
        Gestionnaire des utilisateurs : messages et actions administratives.
    """
    def __init__(self, user_signal):
        """
        Attributs :
            - connected_users: Dictionnaire des utilisateurs connectés.
            - message_queues: Dictionnaire des files d'attente de messages pour chaque utilisateur.
            - lock: Verrou pour assurer la synchronisation des opérations sur les utilisateurs.
            - user_signal: Instance de la classe UserSignal pour émettre des signaux de mise à jour des utilisateurs.
            - kicked_users: Dictionnaire des utilisateurs actuellement kickés et leur durée.
            - banned_users: Dictionnaire des utilisateurs bannis.
            - shutdown_requested: Booléen indiquant si l'arrêt du serveur a été demandé.
            - db_connection: Connexion à la base de données MySQL.
        """
        self.connected_users = {}
        self.message_queues = {}
        self.lock = threading.Lock()
        self.user_signal = user_signal
        self.kicked_users = {}
        self.banned_users = {}
        self.shutdown_requested = False

        # Configuration de la connexion à la base de données MySQL.
        self.db_connection = mysql.connector.connect(
            host="127.0.0.1",
            user="serv302",
            password="serv2024",
            database="sae302"
        )

        self.create_messages_table()
        self.create_banned_users_table()

    # Fonction diffusant le message reçu au serveur à tous les utilisateurs connectés, sauf à l'expéditeur.
    def broadcast_message(self, message, sender_username):
        with self.lock:
            for user_data in self.connected_users.values():
                user_socket = user_data['socket']
                target_username = self.get_username_from_socket(user_socket)
                if target_username != sender_username and target_username not in self.kicked_users and target_username not in self.banned_users:
                    user_socket.send(message.encode('utf-8'))

    # Fonction diffusant un message d'arrêt du serveur à tous les utilisateurs lorsque la commande "kill" est appelé"
    def broadcast_server_shutdown(self):
        shutdown_message = "Attention le serveur va s'arrêter !"
        self.broadcast_message(shutdown_message, sender_username="Server")
        with self.lock:
            for user_data in self.connected_users.values():
                user_socket = user_data['socket']
                user_socket.send(shutdown_message.encode('utf-8'))

    # Fonction créant la table des messages dans la base de données.
    def create_messages_table(self):
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS messages (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                username VARCHAR(255),
                                address VARCHAR(255),
                                message TEXT,
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)

    # Fonction ajoutant le message reçu par le serveur à la base de données.
    def add_message_to_db(self, username, address, message):
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                   INSERT INTO messages (username, address, message) VALUES (%s, %s, %s)
               """, (username, address, message))
        self.db_connection.commit()

    # Fonction créant la table des utilisateurs bannis dans la base de données.
    def create_banned_users_table(self):
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS banned_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    # Fonction ajoutant un utilisateur à la liste des utilisateurs connectés.
    def add_user(self, username, address, client_socket):
        self.connected_users[username] = {'address': address, 'socket': client_socket}
        self.message_queues[username] = queue.Queue()
        self.user_signal.user_updated.emit()

    # Fonction supprimant un utilisateur de la liste des utilisateurs connectés.
    def remove_user(self, username):
        if username in self.connected_users:
            del self.connected_users[username]
            del self.message_queues[username]
            self.user_signal.user_updated.emit()

    # Fonction obtenant le nom d'utilisateur associé à un socket client.
    def get_username_from_socket(self, client_socket):
        for username, data in self.connected_users.items():
            if data['socket'] == client_socket:
                return username
        return None

    # Fonction "Kickant" un utilisateur pour une durée spécifiée.
    def kick_user(self, username, duration):
        kick_message = f"Server : {username} a été kick pendant {duration}"
        self.broadcast_message(kick_message, sender_username="Server")
        self.kicked_users[username] = time.time() + self.parse_duration(duration)

        # Lance un minuteur dans un thread séparé pour ne pas bloquer le thread principal.
        threading.Thread(target=self.kick_timer, args=(username,)).start()
        # Marquer l'utilisateur comme "kické" pour la durée spécifiée.
        self.user_signal.user_updated.emit()

    # Fonction "Timer" pour lever le kick après la durée spécifiée.
    def kick_timer(self, username):
        time.sleep(self.kicked_users[username] - time.time())
        if username in self.kicked_users:
            del self.kicked_users[username]
            self.user_signal.user_updated.emit()

    # Fonction analysant une chaîne de durée au format "1h", "5m", "10s" en secondes.
    def parse_duration(self, duration):
        unit = duration[-1].lower()
        value = int(duration[:-1])
        if unit == 'h':
            return value * 3600
        elif unit == 'm':
            return value * 60
        elif unit == 's':
            return value
        else:
            return 0

    # Fonction vérifiant si un utilisateur est actuellement kické.
    def is_kicked(self, username):
        return username in self.kicked_users

    # Fonction bannissant un utilisateur du serveur.
    def ban_user(self, username):
        ban_message = f"Server: {username} a été banni"
        self.broadcast_message(ban_message, sender_username="Server")
        self.banned_users[username] = True

        # Ajoute l'utilisateur banni à la table des utilisateurs bannis.
        self.add_banned_user_to_db(username)
        # Marque l'utilisateur comme "banni"
        self.user_signal.user_updated.emit()

    # Méthode ajoutant un utilisateur banni à la base de données.
    def add_banned_user_to_db(self, username):
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO banned_users (username) VALUES (%s)
            """, (username,))
        self.db_connection.commit()

    # Fonction vérifiant si un utilisateur est actuellement banni.
    def is_banned(self, username):
        return username in self.banned_users

    # Fonction envoyant un message d'arrêt à tous les clients et demande l'arrêt du serveur.
    def kill_server(self):
        # Envoie un message d'arrêt à tous les clients.
        self.broadcast_server_shutdown()

        # Indique que l'arrêt du serveur a été demandé.
        self.shutdown_requested = True

        # Attend que tous les threads clients se terminent avant de terminer le programme.
        for client_thread in threading.enumerate():
            if isinstance(client_thread, ClientHandler):
                client_thread.join()

    # Fonction émettant un signal de mise à jour des utilisateurs.
    def user_updated(self):
        self.user_signal.user_updated.emit()

class ServerThread(QThread):
    """
            Thread principal du serveur qui accepte les connexions des clients et les gère.
            Attribut :
            - user_manager: Instance de la classe UserManager pour la gestion des utilisateurs.
    """
    def __init__(self, user_manager):
        """
            __init__: Initialise le thread du serveur.
        """
        super().__init__()
        self.user_manager = user_manager

    # Fonction gérant les messages reçus par le client.
    def handle_client_messages(self, client_socket, username):
        try:
            address = client_socket.getpeername()
            print(f"{username} connecté à l'adresse {address}")
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                print(f"Reçu de {username}: {message}")

                if "@ServerShutdown@" in message:
                    print("Arrêt du serveur initié. Fermeture de la connexion client.")
                    break

                # Formatage du message.
                formatted_message = f"@{username}: {message}"
                print(f"Meessage formaté: {formatted_message}")

                # Envoi le message à la database.
                self.user_manager.add_message_to_db(username, "", message)
                self.message_received.emit(formatted_message)

                # Envoi le message en broadcast à tout les clients.
                self.user_manager.broadcast_message(formatted_message, sender_username=username)

        except Exception as e:
            print(f"Gestion des erreurs dans les messages du client pour {username}: {e}")
        finally:
            if client_socket.fileno() != -1:
                client_socket.close()
            self.user_manager.remove_user(username)
            print(f"{username} déconnecté.")
            self.user_manager.user_signal.user_updated.emit()

    # Méthode principale du thread qui accepte les connexions et gère les clients.
    def run(self):
        host = "0.0.0.0"
        port = 9000
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)

        print(f"Serveur à l'écoute sur {host}:{port}")

        try:
            while not self.user_manager.shutdown_requested:
                client_socket, address = server_socket.accept()
                username = client_socket.recv(1024).decode()
                print(f"{username} connecté à l'adresse {address}")
                self.user_manager.add_user(username, address, client_socket)

                # Envoie l'accusé de réception après l'ajout de l'utilisateur.
                client_socket.send("ACK_USERNAME".encode())

                if not self.user_manager.shutdown_requested:
                    # Créer une instance de ClientHandler.
                    client_handler = ClientHandler(username, client_socket, self.user_manager)

                    # Envoie ClientHandler vers un autre thread.
                    thread = QThread(self)
                    client_handler.moveToThread(thread)
                    client_handler.message_received.connect(self.handle_message_received)

                    # Démarrage du thread.
                    thread.started.connect(client_handler.handle_client_messages)
                    thread.start()
        except Exception as e:
            print(f"Erreur du serveur: {e}")
        finally:
            server_socket.close()

    # Fonction gérant un message reçu par le client.
    def handle_message_received(self, message):
        print(f"Message reçu : {message}")
        username, _, user_message = message.partition(':')
        self.user_manager.add_message_to_db(username.strip(), "", user_message.strip())

        # Envoi le message en broadcast à tout les clients.
        self.user_manager.broadcast_message(message, sender_username=username)

class ServerGUI(QWidget):
    """
        Interface graphique pour l'administration du serveur.

        Attributs:
        - selected_user: Nom de l'utilisateur sélectionné dans l'interface.
        - user_manager: Instance de la classe UserManager pour la gestion des utilisateurs.
        - authenticated: Booléen indiquant si l'utilisateur est authentifié.
    """
    selected_user = None
    def __init__(self, user_manager):
        """
            __init__: Initialise l'interface graphique.
        """
        super().__init__()
        self.user_manager = user_manager
        self.authenticated = False

        # Définition du titre de la fenêtre et de sa taille.
        self.setWindowTitle("Administration")
        self.setGeometry(300, 300, 400, 200)

        # Déclaration des boutons (kick, ban, kill) comme des attributs de classe.
        self.kick_button = QPushButton("Kicker l'utilisateur sélectionné", self)
        self.ban_button = QPushButton("Bannir l'utilisateur sélectionné", self)
        self.kill_button = QPushButton("Kill le serveur", self)
        self.init_ui()

    # Fonction initialisant les composants de l'interface utilisateur.
    def init_ui(self):
        layout = QVBoxLayout()

        # Connexion du signal "ClientHandler" à la méthode "update_messages".
        for user_data in self.user_manager.connected_users.values():
            user_handler = user_data['handler']
            user_handler.message_received.connect(partial(self.update_messages, user_data['username']))

        self.user_list = QListWidget(self)
        self.refresh_user_list()
        self.kick_button.setStyleSheet("background-color: #FFAA00; color: white;")
        self.ban_button.setStyleSheet("background-color: #EC2D0B; color: white;")
        self.kill_button.setStyleSheet("background-color: #0BE9EC; color: white;")

        # Connexion des boutons à leurs méthodes respectives.
        self.kick_button.clicked.connect(self.kick_user)
        self.ban_button.clicked.connect(self.ban_user)
        self.kill_button.clicked.connect(self.kill_server)

        layout.addWidget(self.user_list)
        layout.addWidget(self.kick_button)
        layout.addWidget(self.ban_button)
        layout.addWidget(self.kill_button)
        self.setLayout(layout)

        # Connexion du signal "itemClicked" à une fonction pour enregistrer l'utilisateur sélectionné.
        self.user_list.itemClicked.connect(self.select_user)

        # Création d'un Timer pour rafraîchir la liste des utilisateurs toutes les secondes.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_user_list)
        self.timer.start(1000)

    # Méthode pour l'authentification de l'administrateur.
    def authenticate(self):
        # Nom d'utilisateur et mot de passe à utiliser pour l'administrateur.
        correct_username = "admin"
        correct_password = "serv2024!"

        # Vérifie si l'utilisateur est authentifié avant de traiter les messages.
        if not self.authenticated:
            auth_dialog = AuthDialog()
            if auth_dialog.exec() == QDialog.DialogCode.Accepted:
                self.authenticated = True
            else:
                sys.exit(0)

    # Met à jour l'affichage des messages dans l'interface.
    def update_messages(self, username, message):
        # Vérifie si l'utilisateur est authentifié avant de traiter les messages.
        if self.authenticated:
            print(message)

    # Fonction enregistrant l'utilisateur sélectionné dans la variable de classe.
    def select_user(self, item):
        ServerGUI.selected_user = item.text()

    # Fonction rafraichissant la liste des utilisateurs connectés dans l'interface.
    def refresh_user_list(self):
        current_item = self.user_list.currentItem()
        self.user_list.clear()
        users = list(self.user_manager.connected_users.keys())
        self.user_list.addItems(users)

        if self.selected_user is not None and self.selected_user in users:
            index = users.index(self.selected_user)
            item = self.user_list.item(index)
            self.user_list.setCurrentItem(item)
        elif current_item is not None:
            self.user_list.setCurrentItem(current_item)

    # Fonction "Kickant" l'utilisateur sélectionné.
    def kick_user(self):
        # Vérifie si l'utilisateur est authentifié avant d'exécuter la commande.
        if self.authenticated:
            selected_item = self.user_list.currentItem()
            if selected_item is not None:
                ServerGUI.selected_user = selected_item.text()
                duration = "1h"
                self.user_manager.kick_user(ServerGUI.selected_user, duration)
                self.refresh_user_list()
            else:
                print("Aucun utilisateur sélectionné.")

    # Fonction "Bannissant" l'utilisateur sélectionné.
    def ban_user(self):
        # Vérifie si l'utilisateur est authentifié avant d'exécuter la commande.
        if self.authenticated:
            selected_user = self.user_list.currentItem().text()
            self.user_manager.ban_user(selected_user)

    # Fonction arrêtant le serveur et l'application.
    def kill_server(self):
        # Vérifie si l'utilisateur est authentifié avant d'exécuter la commande
        if self.authenticated:
            self.user_manager.kill_server()
            sys.exit()

class ClientHandler(QObject):
    """
        Gestionnaire de messages pour chaque client connecté.

        Attributs:
        - username: Nom d'utilisateur du client.
        - client_socket: Socket de communication avec le client.
        - user_manager: Instance de la classe UserManager pour la gestion des utilisateurs.

        Signal:
        - message_received: Signal émis lorsqu'un message est reçu du client.
    """
    message_received = pyqtSignal(str)
    def __init__(self, username, client_socket, user_manager):
        """
            __init__: Initialise le gestionnaire de messages.
        """
        super().__init__()
        self.username = username
        self.client_socket = client_socket
        self.user_manager = user_manager

    # Fonction envoyant un message au serveur.
    def send_message_to_server(self, message):
        try:
            self.client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Erreur lors de l'envoi d'un message au serveur pour {self.username}: {e}")

    # Fonction gérant les messages reçus du client.
    def handle_client_messages(self):
        try:
            address = self.client_socket.getpeername()
            print(f"{self.username} connecté à l'adresse {address}")

            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                print(f"Reçu de {self.username}: {message}")

                if "@ServerShutdown@" in message:
                    print("Arrêt du serveur initié. Fermeture de la connexion client.")
                    break

                # Formatage du message.
                formatted_message = f"@{self.username}: {message}"
                print(f"Message formaté: {formatted_message}")

                self.user_manager.add_message_to_db(self.username, "", message)

                # Envoi le message au serveur pour "broadcast".
                self.send_message_to_server(formatted_message)

                # Envoi le message en broadcast à tout les clients connectés.
                self.user_manager.broadcast_message(formatted_message, sender_username=self.username)

        except Exception as e:
            print(f"Gestion des erreurs dans les messages du client pour {self.username}: {e}")
        finally:
                if self.client_socket.fileno() != -1:
                    self.client_socket.close()

        self.user_manager.remove_user(self.username)
        print(f"{self.username} déconnecté.")
        self.user_manager.user_signal.user_updated.emit()

    # Méthode principale exécutée dans un thread pour gérer les clients.
    def run(self):
        try:
            address = self.client_socket.getpeername()
            print(f"{self.username} connecté depuis {address}")

            while True:
                # Vérifie si l'utilisateur est "kické" ou "banni".
                if self.user_manager.is_kicked(self.username):
                    kick_message = "Vous avez été Kické, veuillez réessayer plus tard."
                    self.client_socket.send(kick_message.encode())
                    break

                if self.user_manager.is_banned(self.username):
                    ban_message = "Vous avez été banni du serveur."
                    self.client_socket.send(ban_message.encode())
                    break

                self.client_socket.send("ACK_USERNAME".encode())
                self.handle_client_messages()

        except Exception as e:
            print(f"Erreur de gestion du client {self.username}: {e}")
        finally:
            self.user_manager.remove_user(self.username)
            print(f"{self.username} déconnecté.")
            self.client_socket.close()
            self.user_manager.user_signal.user_updated.emit()

def main():
    """
            Fonction principale pour lancer l'application du serveur de chat asynchrone.

            Crée une instance de l'application PyQt, du gestionnaire d'utilisateurs et du thread du serveur.
            Lance l'interface graphique et démarre le thread du serveur.
    """
    app = QApplication(sys.argv)

    # Authentification réussie, créer le gestionnaire d'utilisateurs et démarre le serveur.
    user_signal = UserSignal()
    user_manager = UserManager(user_signal)

    # Démarre le thread du serveur.
    server_thread = ServerThread(user_manager)
    server_thread.start()

    server_gui = ServerGUI(user_manager=user_manager)
    server_gui.authenticate()

    server_gui.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()