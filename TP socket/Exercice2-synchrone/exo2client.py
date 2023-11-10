import socket

# Créer un socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Adresse IP et port du serveur auquel se connecter
server_address = ('127.0.0.1', 6500)

try:
    # Tentative de connexion au serveur
    client_socket.connect(server_address)

    while True:
        # Envoyez un message au serveur
        client_message = input("Message du client : ")
        client_socket.send(client_message.encode('utf-8'))

        if client_message == "arret":
            print("Le client a été arrêté par le client")
            break
        elif client_message == "bye":
            # Arrêtez le client
            print("Le client s'est déconnecté")
            client_socket.close()
            break

        # Recevez la réponse du serveur
        try:
            server_response = client_socket.recv(1024).decode('utf-8')
            print(f"Serveur dit : {server_response}")
        except ConnectionAbortedError:
            print("La connexion a été abandonnée par l'hôte distant")
            break

except ConnectionRefusedError:
    print("La connexion au serveur a été refusée. Assurez-vous que le serveur est en cours d'exécution.")
except ConnectionResetError:
    print("La connexion a été fermée par l'hôte distant")

# Fermez le socket client
client_socket.close()