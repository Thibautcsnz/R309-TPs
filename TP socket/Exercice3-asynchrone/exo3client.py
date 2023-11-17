# Client relatif à l'exercice3 des sockets
import socket
import threading

def receive_messages(client_socket):
    # Définition gérant les messages reçus par le serveur
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"Received from server: {data.decode('utf-8')}")

def send_messages(client_socket):
    # Définition gérant les messages reçus par le client
    while True:
        message = input("Enter message: ")
        client_socket.send(message.encode('utf-8'))

def main():
    # Configuration du Client avec l'Adresse IP et du Port
    host = "127.0.0.1"
    port = 9000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Démarrage du thread gérant les messages arrivant depuis le serveur
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    # Démarrage du thread gérant les messages envoyées depuis le client
    send_thread = threading.Thread(target=send_messages, args=(client_socket,))
    send_thread.start()

    receive_thread.join()
    send_thread.join()

    client_socket.close()

if __name__ == "__main__":
    main()
