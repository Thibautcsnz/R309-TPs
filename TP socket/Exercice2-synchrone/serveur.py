import socket

def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 6500
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 6500))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    print("Connection from: " + str(address))
    while True:
        data = conn.recv(1024).decode()
        print("from connected user: " + str(data))
        data = input(' -> ')
        conn.send(data.encode())
    conn.close()
if __name__ == '__main__':
    server_program()