from flask import Blueprint


utils = Blueprint('utils', __name__)

from . import custom_filters
