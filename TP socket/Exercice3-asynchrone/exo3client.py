import time
import socket
import selectors
import threading

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

def start_client():
    # Créez un socket client
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connectez-vous au serveur
    host = '127.0.0.1'  # Adresse IP du serveur
    port = 6500  # Port à utiliser

    # Ajoutez une pause ici pour laisser le serveur démarrer
    time.sleep(2)

    try:
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
    except ConnectionRefusedError:
        print("Le serveur n'est pas encore prêt à accepter la connexion.")

    server_socket.close()

if __name__ == "__main__":
    start_client()


