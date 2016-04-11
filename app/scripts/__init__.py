from flask import Blueprint

scripts = Blueprint('scripts', __name__)

from .tradunio import update
