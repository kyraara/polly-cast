from flask import Blueprint
riwayat_bp = Blueprint('riwayat', __name__)
from app.blueprints.riwayat import routes
