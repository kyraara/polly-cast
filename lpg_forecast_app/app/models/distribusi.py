from app.extensions import db

class Distribusi(db.Model):
    __tablename__ = 'tbl_distribusi'
    
    id_distribusi = db.Column(db.Integer, primary_key=True)
    periode_tanggal = db.Column(db.Date, nullable=False, unique=True)
    jumlah_distribusi = db.Column(db.Integer, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'))
