# Exercice3 du TP sur les Sockets, le serveur doit gérer un client de manière asynchrone.
# Serveur relatif à l'exercice3 des sockets

import socket
import threading

def handle_client(client_socket):
    # Définition gérant les messages reçus du client
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"Received from client: {data.decode('utf-8')}")

def send_messages(client_socket):
    # Définition gérant les messages envoyées depuis le serveur vers le Client
    while True:
        message = input("Entrez votre message: ")
        client_socket.send(message.encode('utf-8'))


def main():
    # Configuration du serveur avec son adresse IP et son port
    host = "127.0.0.1"
    port = 9000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, address = server_socket.accept()

        # Démarrage du thread qui gère les messagas arrivant du client
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

        # Démarrage du thread qui gère les messages envoyés
        send_thread = threading.Thread(target=send_messages, args=(client_socket,))
        send_thread.start()

if __name__ == "__main__":
    main()

"""
connecté = False
def réception(conn):
    msg=""
    while msg!="by" and message !="arret":
        msg = conn.recv(1024).decode()
        print(msg)
    conn.send(msg)

if __name__ == '__main__'
    server_socket = ________
    server_socket.listen(1)
    msg=""
    while msg!="arret"
        conn, addr=server_socket.accept()
        t1 = Threading(target="reception")
                            args=[conn]
        t1.start()
        msg=""
        while msg!="arret" and msg!="bye"
            and connecte:
                msg=input("")
                conn.send(msg)
        t1.join
        conn.close()
"""