from datetime import datetime
from app.extensions import db

class EvaluasiModel(db.Model):
    __tablename__ = 'tbl_evaluasi_model'
    
    id_evaluasi = db.Column(db.Integer, primary_key=True)
    tanggal_evaluasi = db.Column(db.DateTime, default=datetime.utcnow)
    mae_sarima = db.Column(db.Float)
    rmse_sarima = db.Column(db.Float)
    mape_sarima = db.Column(db.Float)
    mae_hw = db.Column(db.Float)
    rmse_hw = db.Column(db.Float)
    mape_hw = db.Column(db.Float)
    model_terbaik = db.Column(db.String(20))  # 'SARIMA' atau 'Holt-Winters'
    id_user = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'))
    is_hidden = db.Column(db.Boolean, default=False)
    
    # Relationships
    peramalan = db.relationship('Peramalan', backref='evaluasi', lazy=True)
