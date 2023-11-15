import socket
import threading

def receive_messages(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"Received from server: {data.decode('utf-8')}")

def send_messages(client_socket):
    while True:
        message = input("Enter message: ")
        client_socket.send(message.encode('utf-8'))

def main():
    host = "127.0.0.1"
    port = 9000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Start a thread to receive messages from the server
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    # Start a thread to send messages to the server
    send_thread = threading.Thread(target=send_messages, args=(client_socket,))
    send_thread.start()

    receive_thread.join()
    send_thread.join()

    client_socket.close()

if __name__ == "__main__":
    main()

import socket
import threading

def receive_messages(client_socket):
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        decoded_data = data.decode('utf-8')
        print(f"Received from server: {decoded_data}")

        # Protocole
        if decoded_data.lower() == "bye":
            print("Server requested to stop, but client will keep running.")
            break
        elif decoded_data.lower() == "arret":
            print("Server requested to stop. Client will also stop.")
            break

def send_messages(client_socket):
    while True:
        message = input("Enter message: ")
        client_socket.send(message.encode('utf-8'))

        # Protocole
        if message.lower() == "arret":
            print("Client requested to stop. Server will also stop.")
            break

def main():
    host = "127.0.0.1"
    port = 6500

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Start a thread to receive messages from the server
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    # Start a thread to send messages to the server
    send_thread = threading.Thread(target=send_messages, args=(client_socket,))
    send_thread.start()

    receive_thread.join()
    send_thread.join()

    client_socket.close()

if __name__ == "__main__":
    main()

