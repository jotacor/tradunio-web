from flask import Blueprint

tradunio = Blueprint('tradunio', __name__)

from . import update
