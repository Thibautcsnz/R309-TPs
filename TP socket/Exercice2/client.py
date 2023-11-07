import socket

client_socket = socket.socket()
client_socket.connect(("192.168.71.40", 6500))
client_socket.send(message.encode())
reply = client_socket.recv(1024).decode()
client_socket.close()