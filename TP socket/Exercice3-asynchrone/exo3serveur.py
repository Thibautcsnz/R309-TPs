#Exercice3 du TP sur les Sockets, le serveur doit gérer un client de manière asynchrone.

import socket
import threading

# Liste pour stocker les connexions client
client_connections = []

def handle_client(client_socket):
    try:
        while True:
            # Données reçues par le client
            client_data = client_socket.recv(1024).decode('utf-8')
            print(f"Client dit : {client_data}")

            if client_data == "arret":
                print("Le serveur a été arrêté par le client")
                client_socket.send("arret".encode('utf-8'))  # Envoyer un signal d'arrêt au client
                break
            elif client_data == "bye":
                print("Le client s'est déconnecté")
                break

            # Envoyez une réponse au client
            try:
                server_response = input("Réponse du serveur : ")
            except KeyboardInterrupt:
                print("\nInterruption du serveur. Arrêt en cours...")
                break

            client_socket.send(server_response.encode('utf-8'))
    except ConnectionResetError:
        print("La connexion a été fermée par l'hôte distant")

    # Fermez le socket client
    client_socket.close()

def start_server():
    # Créez un socket serveur
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Liez le socket à une adresse et un port
    host = '127.0.0.1'  # Adresse IP du serveur
    port = 6500  # Port à utiliser

    try:
        server_socket.bind((host, port))
    except OSError as e:
        if e.errno == 10048:
            print(f"Le port {port} est déjà utilisé. Assurez-vous qu'aucun autre programme n'utilise ce port.")
            exit()
        else:
            raise

    # Écoutez les connexions entrantes (maximum de 3 connexions en attente)
    server_socket.listen(3)
    print(f"Le serveur écoute sur {host}:{port}")

    while True:
        # Attendez qu'un client se connecte
        print("En attente d'un client...")
        client_socket, client_address = server_socket.accept()
        print(f"Connexion entrante de {client_address}")

        # Ajoutez la connexion client à la liste
        client_connections.append(client_socket)

        # Lancez un thread pour gérer le client
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_server()

def receive_from_server(server_socket):
    try:
        while True:
            # Recevez des données du serveur
            server_data = server_socket.recv(1024).decode('utf-8')
            print(f"Réponse du serveur : {server_data}")

            if server_data == "arret" or server_data == "bye":
                print("Le serveur s'est déconnecté")
                break
    except ConnectionResetError:
        print("La connexion a été fermée par le serveur")
    finally:
        # Fermez le socket client
        server_socket.close()

def send_to_server(server_socket):
    try:
        while True:
            # Envoyez un message au serveur depuis le client
            client_message = input("Client dit : ")
            server_socket.send(client_message.encode('utf-8'))

            if client_message.lower().strip() == 'arret':
                print("Le client demande l'arrêt du serveur.")
                break
    except ConnectionResetError:
        print("La connexion a été fermée par le serveur")
    finally:
        # Fermez le socket client
        server_socket.close()

def start_client():
    # Créez un socket client
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connectez-vous au serveur
    host = '127.0.0.1'  # Adresse IP du serveur
    port = 6500  # Port à utiliser

    server_socket.connect((host, port))
    print(f"Connecté au serveur {host}:{port}")

    # Créez deux threads distincts pour la réception et l'envoi
    receive_thread = threading.Thread(target=receive_from_server, args=(server_socket,))
    send_thread = threading.Thread(target=send_to_server, args=(server_socket,))

    # Lancez les threads
    receive_thread.start()
    send_thread.start()

    # Attendez la fin des threads avant de fermer le socket client
    receive_thread.join()
    send_thread.join()

    server_socket.close()

if __name__ == "__main__":
    start_client()
