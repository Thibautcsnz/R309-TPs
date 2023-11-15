#Exercice3 du TP sur les Sockets, le serveur doit gérer un client de manière asynchrone.

import socket
import threading

def handle_client(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"Received from client: {data.decode('utf-8')}")


def send_messages(client_socket):
    while True:
        message = input("Entrez votre message: ")
        client_socket.send(message.encode('utf-8'))


def main():
    host = "127.0.0.1"
    port = 9000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, address = server_socket.accept()

        # Start a thread to handle the client's incoming messages
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

        # Start a thread to send messages to the client
        send_thread = threading.Thread(target=send_messages, args=(client_socket,))
        send_thread.start()


if __name__ == "__main__":
    main()