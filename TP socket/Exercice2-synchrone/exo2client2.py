import socket
# Client2 de l'exercice 2 (synchrone) des sockets
# Mise en place du socket Client
client2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Adresse IP | port du serveur auquel se connecter
server_address = ('127.0.0.1', 8000)

try:
    # Tentative de connexion au serveur
    client2_socket.connect(server_address)

    while True:
        # Envoie du message au serveur
        client2_message = input("Message du client : ")
        client2_socket.send(client2_message.encode('utf-8'))
        # Messages bye et arret
        if client2_message == "arret":
            print("Le client a été arrêté par le client")
            break
        elif client2_message == "bye":
            # Arrêtez du client lorsque celui-ci envoie "bye"
            print("Le client s'est déconnecté")
            client2_socket.close()
            break

        # Réponse du serveur
        try:
            server_response = client2_socket.recv(1024).decode('utf-8')
            print(f"Serveur dit : {server_response}")
        # Exception relative à l'arrêt de la connexion
        except ConnectionAbortedError:
            print("La connexion a été abandonnée par l'hôte distant")
            break
#Exception relative du fait que le serveur n'autorise pas la connexion
except ConnectionRefusedError:
    print("La connexion au serveur a été refusée. Assurez-vous que le serveur est en cours d'exécution.")
#Exception relative du fait que le client a fermé la connexion avec le serveur
except ConnectionResetError:
    print("La connexion a été fermée par l'hôte distant")

# Fermeture du socket client
client2_socket.close()