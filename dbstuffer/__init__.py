from app.database import build_db, Machine, Machine_Type, Machine_State, connect_db, Record, Packet_Type
from datetime import datetime
import time, os
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound

menu_options = {
    'x':'exit'
}

def print_menu():
    print('Select an option below:')
    # print('c : connect to an existing database')
    # print('d : create a new database')
    # print('m : create a sample machine')
    print('1 : create a new starting packet')
    print('2 : create a new started packet')
    print('3 : create a new running packet')
    print('4 : create a new shutdown packet')
    print('5 : create a new heartbeat packet')
    # print('s : run scanner')
    print('x : exit')

def make_machine(db,serial_no):
    print("Building a test machine")
    state   = db.query(Machine_State).filter_by(state_name="Stopped").one()
    type    = db.query(Machine_Type).filter_by(type_name="Cake Mixer").one()
    my_machine = Machine(name="Test Machine", location="Home", serial_no=serial_no, state=state, type=type, date_commisioned=datetime.utcnow())
    db.add(my_machine)
    db.commit()

def make_database(db,serial_no):
    print("Making use of a sample database")
    print("Building the configuration of the database...")
    build_db(db)
    print("Done!")

def connect_database(db,serial_no):
    print("Making use of an existing database. Connecting...")
    db = connect_db(os.path.join('c:/users/henri/dropbox/git/DBexperiments/','data.sqlite'))
    print("Done!")


def machine_processor(db,serial_no):
    # print("Thread: Machine Processor: Started")
    thread_db = db
    my_machine = thread_db.query(Machine).filter_by(serial_no=serial_no).one()
    print(my_machine)
    process = True
    while process:
        new_records = thread_db.query(Record).filter_by(machine = my_machine)\
            .filter(Record.packet_timestamp > my_machine.last_update).all()
        if len(new_records) > 0:
            print("New records found (# %s)" % len(new_records))
            for record in new_records:
                print("Processing a %s record" % record.packet_type.packet_name)
                print('Current machine.state is %s' % my_machine.state.state_name)
                try:
                    packet_state = thread_db.query(Machine_State).filter_by(state_name=record.packet_type.packet_name).one()
                    if ((my_machine.state.state_name != 'Stopped') and \
                                (my_machine.state.state_name != 'Error')):
                        print("Updating the running time of te machine")
                        my_machine.running_time += record.packet_timestamp-my_machine.last_update
                        print("Maching runnign time now %s" % my_machine.running_time)
                    my_machine.last_update = record.packet_timestamp
                    my_machine.state = packet_state
                    if (my_machine.state.state_name == "Shutdown"):
                        my_machine.state = thread_db.query(Machine_State).filter_by(state_name="Stopped").one()
                        my_machine.cycles += 1
                    thread_db.commit()
                    print('Machine state updated to %s state' % record.packet_type.packet_name)
                except NoResultFound or MultipleResultsFound:
                    print("Packet does not contain a machine state change")
                    print("Only updating machine timestamp")
                    my_machine.last_update = record.packet_timestamp
        else:
            print("No new records found")
        time.sleep(1)
        process = False
    return False

def starting_packet(db,serial_no):
    print("Making a starting packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Starting').one()
    record = Record(packet_timestamp=datetime.utcnow(), machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

def started_packet(db,serial_no):
    print("Making a started packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Started').one()
    record = Record(packet_timestamp=datetime.utcnow(), machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

def running_packet(db,serial_no):
    print("Making a starting packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Running').one()
    record = Record(packet_timestamp=datetime.utcnow(), machine=machine,
                    packet_type=packet_type, packet_data = 4.1)
    db.add(record)
    db.commit()
    print("Record added")

def shutdown_packet(db,serial_no):
    print("Making a shutdown packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Shutdown').one()
    record = Record(packet_timestamp=datetime.utcnow(), machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

def heartbeat_packet(db,serial_no):
    print("Making a heartbeat packet for machine with serial no %s" % serial_no)
    machine = db.query(Machine).filter_by(serial_no=serial_no).one()
    packet_type = db.query(Packet_Type).filter_by(packet_name='Heartbeat').one()
    record = Record(packet_timestamp=datetime.utcnow(), machine=machine,
                    packet_type=packet_type)
    db.add(record)
    db.commit()
    print("Record added")

if __name__ == "__main__":
    switch={
        # 'c'         :connect_database,
        'd'         :make_database,
        'm'         :make_machine,
        '1'         :starting_packet,
        '2'         :started_packet,
        '3'         :running_packet,
        '4'         :shutdown_packet,
        '5'         :heartbeat_packet,
        's'         :machine_processor,
        'default'   :'unknown menu option'}

    exit = False
    serial_no = 1
    # db = connect_db('')
    db = connect_db('sqlite:///' + os.path.join('c:/users/henri/dropbox/git/prometheus/','data-dev.sqlite'))
    while not exit:
        print_menu()
        usr_input = input('')
        if usr_input != 'x':
            try:
                switch[usr_input](db,serial_no)
            except KeyError:
                print("Error in dictionary")
        else:
            exit = True
    print("Bye Bye")


