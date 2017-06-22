from flask import Blueprint
machines = Blueprint('machines',__name__)

from . import views
