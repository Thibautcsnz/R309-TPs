import socket
#Exercice2 du TP sur les Sockets, le serveur doit gérer deux clients (non simultanés) de manière synchrone.
def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 6500
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 6500))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    print("Connection venant de: " + str(address))
    while True:
        data = conn.recv(1024).decode()
        print("Message du client: " + str(data))
        if data.lower().strip() == 'bye':
            conn.send("Arrêt du client".encode())
        elif data.lower().strip() == 'arret':
            conn.send("Arrêt du client et du serveur".encode())
            conn.close()
            server_socket.close()
            break
        else:
            message = input('Serveur dit : ')
            conn.send(message.encode())
            if message.lower().strip() == 'bye':
                break
    conn.close()
    server_socket.close()

if __name__ == '__main__':
    server_program()
