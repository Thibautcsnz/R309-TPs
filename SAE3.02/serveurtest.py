import sys
import socket
import threading
import time
import queue
from PyQt6.QtGui import QPalette, QColor, QLinearGradient
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget
from clientest import ClientHandler

class UserSignal(QObject):
    user_updated = pyqtSignal()

class UserManager:
    def __init__(self, user_signal):
        self.connected_users = {}
        self.message_queues = {}
        self.lock = threading.Lock()
        self.user_signal = user_signal
        self.kicked_users = {}
        self.banned_users = {}
        self.shutdown_requested = False

    def add_user(self, username, address, client_socket):
        self.connected_users[username] = {'address': address, 'socket': client_socket}
        self.message_queues[username] = queue.Queue()
        self.user_signal.user_updated.emit()

    def remove_user(self, username):
        if username in self.connected_users:
            del self.connected_users[username]
            del self.message_queues[username]
            self.user_signal.user_updated.emit()

    def broadcast_message(self, username, message):
        with self.lock:
            for user_data in self.connected_users.values():
                user_socket = user_data['socket']
                target_username = self.get_username_from_socket(user_socket)
                if target_username not in self.kicked_users and target_username not in self.banned_users:
                    user_socket.send(message.encode('utf-8'))

    def get_username_from_socket(self, client_socket):
        for username, data in self.connected_users.items():
            if data['socket'] == client_socket:
                return username
        return None

    def broadcast_server_shutdown(self):
        shutdown_message = "Attention ! Arrêt du serveur !"
        self.broadcast_message("Server", shutdown_message)
        with self.lock:
            for user_data in self.connected_users.values():
                user_socket = user_data['socket']
                user_socket.send(shutdown_message.encode('utf-8'))

    def kick_user(self, username, duration):
        kick_message = f"Kicked {username} for {duration}"
        self.broadcast_message("Server", kick_message)
        self.kicked_users[username] = time.time() + self.parse_duration(duration)

        # Utilisez un dictionnaire pour stocker les informations sur l'utilisateur "kicked"
        self.kicked_users[username] = time.time() + self.parse_duration(duration)
        self.user_signal.user_updated.emit()

        # Lancer le minuteur dans un thread séparé pour ne pas bloquer le thread principal
        threading.Thread(target=self.kick_timer, args=(username,)).start()

        # Marquer l'utilisateur comme "kicked" pour la durée spécifiée
        self.kicked_users.add(username)
        self.user_signal.user_updated.emit()
        time.sleep(self.parse_duration(duration))
        self.kicked_users.remove(username)
        self.user_signal.user_updated.emit()

    def kick_timer(self, username):
        time.sleep(self.kicked_users[username] - time.time())
        if username in self.kicked_users:
            del self.kicked_users[username]
            self.user_signal.user_updated.emit()

        # Lancer le minuteur dans un thread séparé pour ne pas bloquer le thread principal
        threading.Thread(target=kick_timer).start()

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

    def is_kicked(self, username):
        return username in self.kicked_users

    def ban_user(self, username):
        ban_message = f"Banned {username}"
        self.broadcast_message("Server", ban_message)
        self.banned_users[username] = True

        # Marquer l'utilisateur comme "banned"
        self.banned_users.add(username)
        self.user_signal.user_updated.emit()

    def is_banned(self, username):
        return username in self.banned_users

    def kill_server(self):
        # Envoyez un message d'arrêt à tous les clients
        self.broadcast_server_shutdown()

        # Indiquer que l'arrêt du serveur a été demandé
        self.shutdown_requested = True

        # Attendre que tous les threads clients se terminent avant de terminer le programme
        for client_thread in threading.enumerate():
            if isinstance(client_thread, ClientHandler):
                client_thread.join()

    def user_updated(self):
        self.user_signal.user_updated.emit()

class ServerThread(QThread):
        def __init__(self, user_manager):
            super().__init__()
            self.user_manager = user_manager

        def run(self):
            host = "127.0.0.1"
            port = 9000

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((host, port))
            server_socket.listen(5)

            print(f"Serveur à l'écoute sur {host}:{port}")

            try:
                while not self.user_manager.shutdown_requested:
                    client_socket, address = server_socket.accept()
                    username = client_socket.recv(1024).decode('utf-8')
                    print(f"{username} connecté depuis {address}")
                    self.user_manager.add_user(username, address, client_socket)

                    # Envoyer l'accusé de réception après avoir ajouté l'utilisateur
                    client_socket.send("ACK_USERNAME".encode())

                    if not self.user_manager.shutdown_requested:
                        client_handler = ClientHandler(username, client_socket, self.user_manager)
                        client_handler.start()

            except Exception as e:
                print(f"Erreur du serveur : {e}")
            finally:
                server_socket.close()

class ServerGUI(QWidget):
    selected_user = None
    def __init__(self, user_manager):
        super().__init__()

        self.user_manager = user_manager

        self.setWindowTitle("Administration")
        self.setGeometry(300, 300, 400, 200)
        # Déclarez les boutons comme des attributs de classe
        self.kick_button = QPushButton("Kick Selected User", self)
        self.ban_button = QPushButton("Ban Selected User", self)
        self.kill_button = QPushButton("Kill Server", self)
        self.client_handler = ClientHandler(username, client_socket, address, user_manager, self.input_edit)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.user_list = QListWidget(self)
        self.refresh_user_list()

        self.kick_button.setStyleSheet("background-color: #FFAA00; color: white;")
        self.ban_button.setStyleSheet("background-color: #EC2D0B; color: white;")
        self.kill_button.setStyleSheet("background-color: #0BE9EC; color: white;")

        # Connexion des boutons à leurs méthodes respectives
        self.kick_button.clicked.connect(self.kick_user)
        self.ban_button.clicked.connect(self.ban_user)
        self.kill_button.clicked.connect(self.kill_server)

        layout.addWidget(self.user_list)
        layout.addWidget(self.kick_button)
        layout.addWidget(self.ban_button)
        layout.addWidget(self.kill_button)

        self.setLayout(layout)

        # Connectez le signal itemClicked à une fonction pour enregistrer l'utilisateur sélectionné
        self.user_list.itemClicked.connect(self.select_user)

        # Create a QTimer for refreshing the user list every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_user_list)
        self.timer.start(1000)  # Refresh every 1000 milliseconds (1 second)

    def select_user(self, item):
        # Enregistrez l'utilisateur sélectionné dans la variable de classe
        ServerGUI.selected_user = item.text()

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

    def kick_user(self):
        selected_item = self.user_list.currentItem()
        if selected_item is not None:
            ServerGUI.selected_user = selected_item.text()
            duration = "1h"  # Remplacez par la durée réelle que vous souhaitez définir
            self.user_manager.kick_user(ServerGUI.selected_user, duration)
            self.refresh_user_list()
        else:
            print("Aucun utilisateur sélectionné.")

    def ban_user(self):
        selected_user = self.user_list.currentItem().text()
        self.user_manager.ban_user(selected_user)

    def kill_server(self):
        self.user_manager.kill_server()
        # Add any additional cleanup or shutdown logic here
        sys.exit()

class ClientHandler(threading.Thread):
    def __init__(self, username, client_socket, user_manager):
        super().__init__()
        self.username = username
        self.client_socket = client_socket
        self.user_manager = user_manager

    def handle_client_messages(self):
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                print(f"Reçu de {self.username}: {message}")

                formatted_message = f"{self.username}: {message}"
                self.user_manager.broadcast_message(self.username, formatted_message)

        except Exception as e:
            print(f"Erreur lors de la gestion des messages du client {self.username}: {e}")
        finally:
            self.user_manager.remove_user(self.username)
            print(f"{self.username} déconnecté.")
            self.client_socket.close()
            self.user_manager.user_signal.user_updated.emit()

    def run(self):
        try:
            address = self.client_socket.getpeername()
            print(f"{self.username} connecté depuis {address}")

            while True:
                # Vérifier si l'utilisateur est kické ou banni
                if self.user_manager.is_kicked(self.username):
                    kick_message = "You have been kicked. Please try again later."
                    self.client_socket.send(kick_message.encode())
                    break

                if self.user_manager.is_banned(self.username):
                    ban_message = "You have been banned from the server."
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
    app = QApplication(sys.argv)
    user_signal = UserSignal()
    user_manager = UserManager(user_signal)

    # Start the server thread
    server_thread = ServerThread(user_manager)
    server_thread.start()

    server_gui = ServerGUI(user_manager=user_manager)
    server_gui.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()