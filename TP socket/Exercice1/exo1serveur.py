import socket
# Exercice1 du TP sur les sockets, celui-ci contient un client et un serveur
# Le client et le serveur gèrent, tout deux, des exceptions.
# Serveur de l'exercice1 des sockets
try:
    reply = 'active'
    server_socket = socket.socket()
    server_socket.bind(('127.0.0.1', 6500))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    message = conn.recv(1024).decode()
    conn.send(reply.encode())
    # Exception relative aux sockets
except socket.error as err:
    print(f"Une erreur au niveau du socket est intervenu: {err}")
    # Exeption relative aux exceptions
except Exception as err:
    print(f"Une erreur est survenue: {err}")
finally:
    conn.close()
    server_socket.close()
