import socket
import signal
import sys
from .CGR_protocol import CGR_Type,CGR_Data,CGR_TimeStamp
from .DatabaseModels import build_db, Machine, Machine_Type, Machine_State, connect_db, Record, Packet_Type

def heartbeat_packet(db,serial_no,timestamp):
    print("Making a heartbeat packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Heartbeat').one()
    record = Record(packet_timestamp=timestamp, machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

def starting_packet(db,serial_no,timestamp):
    print("Making a <starting> packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Starting').one()
    record = Record(packet_timestamp=timestamp, machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

def started_packet(db,serial_no,timestamp,data):
    print("Making a <started> packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Started').one()
    record = Record(packet_timestamp=timestamp, machine=machine,
                    packet_type=packet_type, packet_data=data)
    db.add(record)
    db.commit()
    print("Record added")

def running_packet(db,serial_no,timestamp,data):
    print("Making a <running packet %s A> for machine with serial no %s" % (data,serial_no))
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Running').one()
    record = Record(packet_timestamp=timestamp, machine=machine,
                    packet_type=packet_type, packet_data=data)
    db.add(record)
    db.commit()
    print("Record added")

def shutdown_packet(db,serial_no,timestamp):
    print("Making a <Shutdown packet> for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Shutdown').one()
    record = Record(packet_timestamp=timestamp, machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

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
server_address = ('127.0.0.1',54000 )
print('starting up on %s port %s' % server_address)
sock.bind(server_address)
# Listen for incoming connections
sock.listen(1)
print("Trying to connect to DB @ " + 'sqlite:///' + sys.argv[1])
db = connect_db('sqlite:///' + sys.argv[1])
while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        # while True:
        datagram = connection.recv(50)
        hex_string = "".join("[%02x] " % b for b in datagram)
        print('received "%s"' % hex_string)
        machine_serial = datagram[0]
        packet_timestamp = CGR_TimeStamp(datagram)
        if (CGR_Type(datagram) == "Heartbeat"):
            heartbeat_packet(db,machine_serial,packet_timestamp)
        if (CGR_Type(datagram) == "Starting"):
            starting_packet(db,machine_serial,packet_timestamp)
        if (CGR_Type(datagram) == "Started"):
            packet_data = CGR_Data(datagram)
            started_packet(db,machine_serial,packet_timestamp,packet_data)
        if (CGR_Type(datagram) == "Running"):
            packet_data = CGR_Data(datagram)
            running_packet(db,machine_serial,packet_timestamp,packet_data)
        if (CGR_Type(datagram) == "Shutdown"):
            shutdown_packet(db, machine_serial, packet_timestamp)

    finally:
        # Clean up the connection
        connection.close()
