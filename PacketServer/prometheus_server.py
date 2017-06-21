import socket
import signal
import sys

def signal_handler(signal, frame):
    print("Prometheus Packet Server - Get Ctrl-C")
    print("Prometheus Packet Server - Closing the Socket")
    global sock, connection
    try:
        connection.close()
    except:
        pass
    try:
        sock.close()
    except:
        pass
    print("Prometheus Packet Server - All done. Bye Bye")
    sys.exit()

#hook the signal handler

signal.signal(signal.SIGINT,signal_handler)

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

