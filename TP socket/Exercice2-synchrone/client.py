import socket
def client_program():
    host = socket.gethostname()
    port = 6500
    client_socket = socket.socket()
    client_socket.connect(("127.0.0.1", 6500))
    while True:
        message = input(" -> ")
        client_socket.send(message.encode())
        data = client_socket.recv(1024).decode()
        print('Received from server: ' + data)
        if data.lower().strip() == 'arrêt' or data.lower().strip() == 'bye':
            break
    client_socket.close()

if __name__ == '__main__':
    client_program()
