import socket

def client_program():
    host = socket.gethostname()
    port = 6500
    client_socket = socket.socket()
    client_socket.connect(("127.0.0.1", 6500))
    message = input(" -> ")
    while message.lower().strip() != 'bye':
        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print('Received from server: ' + data)
        message = input(" -> ")
    client_socket.close()
    while message.lower().strip() != 'arrêt':
        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print('Received from server: ' + data)
        message = input(" -> ")
    client_socket.close()
    conn.close()
if __name__ == '__main__':
    client_program()