from app.extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'tbl_user'
    
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('kabag_operasional', 'manager'), nullable=False)
    
    # Relationships
    distribusi = db.relationship('Distribusi', backref='user', lazy=True)
    evaluasi = db.relationship('EvaluasiModel', backref='user', lazy=True)

    def get_id(self):
        return str(self.id_user)
