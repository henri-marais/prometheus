import socket
import sys
from packet_server import CGR_protocol as CGRP

packet_1 = bytes([0x01,0x11,0x17,0x06,0x20,0x16,0x43,0x57,0x92,0x00,0x00,0xff]) #heartbeat
packet_2 = bytes([0x01,0x12,0x17,0x06,0x20,0x16,0x44,0x01,0x43,0x00,0x00,0xff]) #starting
packet_3 = bytes([0x01,0x13,0x17,0x06,0x20,0x16,0x44,0x01,0x57,0x32,0x12,0xff]) #started
packet_4 = bytes([0x01,0x14,0x17,0x06,0x20,0x16,0x44,0x01,0x58,0x04,0x20,0xff]) #running
packet_5 = bytes([0x01,0x15,0x17,0x06,0x20,0x16,0x44,0x02,0x38,0x00,0x00,0xff]) #shutdown

print("Packet 1 time: %s, type: %s, data: %s" % (CGRP.CGR_TimeStamp(packet_1),CGRP.CGR_Type(packet_1),CGRP.CGR_Data(packet_1)))
print("Packet 2 time: %s, type: %s, data: %s" % (CGRP.CGR_TimeStamp(packet_2),CGRP.CGR_Type(packet_2),CGRP.CGR_Data(packet_2)))
print("Packet 3 time: %s, type: %s, data: %s" % (CGRP.CGR_TimeStamp(packet_3),CGRP.CGR_Type(packet_3),CGRP.CGR_Data(packet_3)))
print("Packet 4 time: %s, type: %s, data: %s" % (CGRP.CGR_TimeStamp(packet_4),CGRP.CGR_Type(packet_4),CGRP.CGR_Data(packet_4)))
print("Packet 5 time: %s, type: %s, data: %s" % (CGRP.CGR_TimeStamp(packet_5),CGRP.CGR_Type(packet_5),CGRP.CGR_Data(packet_5)))


def send2server(data):
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connect the socket to the port where the server is listening
    server_ip = socket.gethostbyname('www.incidiumgroup.com')
    server_address = (server_ip, 54321)
    print('connecting to %s port %s' % server_address)
    sock.connect(server_address)
    print("Sending packet to server" % data)
    sock.sendall(data)
    sock.close()
    print("Message sent")


send2server(packet_1)
send2server(packet_2)
send2server(packet_3)
send2server(packet_4)
send2server(packet_5)