#!/usr/bin/env python
import os
from app import create_app,celery
from app.extensions import db
from app.models import User,Role,Machine,Record,Packet_Type,Machine_State,Machine_Type
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, celery=celery, Machine=Machine,Record=Record,
                Packet_Type=Packet_Type,Machine_State=Machine_State, Machine_Type=Machine_Type)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
