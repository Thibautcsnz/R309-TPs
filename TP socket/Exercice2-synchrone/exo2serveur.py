import socket
#Exercice2 du TP sur les Sockets, le serveur doit gérer un client de manière synchrone.

# Variable de contrôle pour indiquer si le serveur doit s'arrêter
server_stopped = False

def handle_client(client_socket):
    global server_stopped  # Utilisation de la variable globale

    try:
        while True:
            # Données reçues par le client
            client_data = client_socket.recv(1024).decode('utf-8')
            print(f"Client dit : {client_data}")

            if client_data == "arret":
                print("Le serveur a été arrêté par le client")
                client_socket.send("arret".encode('utf-8'))  # Envoyer un signal d'arrêt au client
                server_stopped = True  # Mettez à jour la variable de contrôle
                break
            elif client_data == "bye":
                print("Le client s'est déconnecté")
                break

            # Envoyez une réponse au client
            try:
                server_response = input("Réponse du serveur : ")
            except KeyboardInterrupt:
                print("\nInterruption du serveur. Arrêt en cours...")
                server_stopped = True
                break

            client_socket.send(server_response.encode('utf-8'))
    except ConnectionResetError:
        print("La connexion a été fermée par l'hôte distant")

    # Fermez le socket client
    client_socket.close()

def start_server():
    global server_stopped  # Utilisation de la variable globale

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

    while not server_stopped:  # Utilisez la variable de contrôle dans la boucle principale
        # Attendez qu'un client se connecte
        print("En attente d'un client...")
        client_socket, client_address = server_socket.accept()
        print(f"Connexion entrante de {client_address}")

        # Gérez le client sans utiliser de thread
        handle_client(client_socket)

    # Fermez le socket serveur après l'arrêt
    server_socket.close()

if __name__ == "__main__":
    start_server()