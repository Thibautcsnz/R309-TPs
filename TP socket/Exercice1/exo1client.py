# Client1 relatif à l'exercice1 des sockets
import socket
try:
    message = 'salut'
    client_socket = socket.socket()
    client_socket.connect(("127.0.0.1", 6500))
    client_socket.send(message.encode())
    reply = client_socket.recv(1024).decode()
    # Exception relative aux sockets
except socket.error as err:
    print(f"Une erreur au niveau du socket est intervenu: {err}")
    # Exception relative aux erreurs
except Exception as err:
    print(f"Une erreur est survenue: {err}")
finally:
    client_socket.close()