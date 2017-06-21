import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('0.0.0.0', 54000)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)
# Listen for incoming connections
sock.listen(1)
while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        # while True:
        data = connection.recv(50)
        hex_string = "".join("[%02x] " % b for b in data)
        print('received "%s"' % hex_string)
            # if data:
            #     print >> sys.stderr, 'sending data back to the client'
            #     connection.sendall(data)
            # else:
            #     print >> sys.stderr, 'no more data from', client_address
            #     break

    finally:
        # Clean up the connection
        connection.close()

