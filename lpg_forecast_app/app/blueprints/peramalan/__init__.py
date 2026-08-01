from flask import Blueprint

peramalan_bp = Blueprint('peramalan', __name__)

from app.blueprints.peramalan import routes
