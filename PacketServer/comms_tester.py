import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_ip = socket.gethostbyname('www.incidiumgroup.com')
server_address = (server_ip, 54000)
print('connecting to %s port %s' % server_address)
sock.connect(server_address)
message = "Hello Server!"
print("Sending %s to server" % message)
sock.sendall(message)
print("Message sent")
sock.close()
