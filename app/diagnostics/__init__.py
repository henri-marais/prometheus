from flask import Blueprint
diagnostics = Blueprint('diagnostics',__name__)

from . import views
