import socket

# Créer un socket client
client2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Adresse IP et port du serveur auquel se connecter
server_address = ('127.0.0.1', 6500)

try:
    # Tentative de connexion au serveur
    client2_socket.connect(server_address)

    while True:
        # Envoyez un message au serveur
        client2_message = input("Message du client : ")
        client2_socket.send(client2_message.encode('utf-8'))

        if client2_message == "arret":
            print("Le client a été arrêté par le client")
            break
        elif client2_message == "bye":
            # Arrêtez le client
            print("Le client s'est déconnecté")
            client2_socket.close()
            break

        # Recevez la réponse du serveur
        try:
            server_response = client2_socket.recv(1024).decode('utf-8')
            print(f"Serveur dit : {server_response}")
        except ConnectionAbortedError:
            print("La connexion a été abandonnée par l'hôte distant")
            break

except ConnectionRefusedError:
    print("La connexion au serveur a été refusée. Assurez-vous que le serveur est en cours d'exécution.")
except ConnectionResetError:
    print("La connexion a été fermée par l'hôte distant")

# Fermez le socket client
client2_socket.close()