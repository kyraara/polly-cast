from flask import Blueprint

distribusi_bp = Blueprint('distribusi', __name__)

from app.blueprints.distribusi import routes
