from app.extensions import db

class Peramalan(db.Model):
    __tablename__ = 'tbl_peramalan'
    
    id_peramalan = db.Column(db.Integer, primary_key=True)
    id_evaluasi = db.Column(db.Integer, db.ForeignKey('tbl_evaluasi_model.id_evaluasi'))
    periode_prediksi = db.Column(db.Date, nullable=False)
    nilai_prediksi_sarima = db.Column(db.Float)
    nilai_prediksi_hw = db.Column(db.Float)
