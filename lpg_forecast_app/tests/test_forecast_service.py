import pytest
import pandas as pd
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.distribusi import Distribusi
from app.services.forecast_service import ForecastService

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(username='testuser', password_hash='hash', role='kabag_operasional')
        db.session.add(user)
        db.session.commit()
        
        # Seed dummy data (24 months)
        start_date = pd.to_datetime('2020-01-01')
        for i in range(24):
            curr_date = (start_date + pd.DateOffset(months=i)).date()
            val = 1000000 + (i * 5000) + (10000 if i % 12 == 5 else 0)
            dist = Distribusi(periode_tanggal=curr_date, jumlah_distribusi=val, id_user=user.id_user)
            db.session.add(dist)
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

def test_forecast_pipeline(app):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        payload = ForecastService.run_forecast(user.id_user, n_periods_ahead=12)
        
        assert payload['id_evaluasi'] is not None
        assert len(payload['labels_historical']) == 24
        assert len(payload['labels_future']) == 12
        assert len(payload['pred_future_sarima']) == 12
        assert len(payload['pred_future_hw']) == 12
        assert payload['metrics']['model_terbaik'] in ['SARIMA', 'Holt-Winters']

def test_forecast_force_retrain(app):
    import os
    import json
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        payload = ForecastService.run_forecast(user.id_user, n_periods_ahead=12, force_retrain=True)
        
        assert payload['id_evaluasi'] is not None
        
        collab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'models', 'collab'))
        metadata_path = os.path.join(collab_dir, 'models_metadata.json')
        
        assert os.path.exists(metadata_path)
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        assert metadata['dataset_info']['count'] == 24
        assert metadata['dataset_info']['last_date'] is not None

def test_forecast_insufficient_data(app):
    with app.app_context():
        # Clear data
        Distribusi.query.delete()
        db.session.commit()
        
        user = User.query.filter_by(username='testuser').first()
        with pytest.raises(ValueError) as excinfo:
            ForecastService.run_forecast(user.id_user, n_periods_ahead=12)
        assert "Data distribusi terlalu sedikit" in str(excinfo.value)
