from flask import Blueprint

evaluasi_bp = Blueprint('evaluasi', __name__)

from app.blueprints.evaluasi import routes
