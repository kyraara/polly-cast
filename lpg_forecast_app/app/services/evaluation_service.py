import numpy as np
from app.models.evaluasi_model import EvaluasiModel

class EvaluationService:
    @staticmethod
    def hitung_mae(actual, forecast):
        actual = np.array(actual)
        forecast = np.array(forecast)
        return float(np.mean(np.abs(actual - forecast)))

    @staticmethod
    def hitung_rmse(actual, forecast):
        actual = np.array(actual)
        forecast = np.array(forecast)
        return float(np.sqrt(np.mean((actual - forecast) ** 2)))

    @staticmethod
    def hitung_mape(actual, forecast):
        actual = np.array(actual)
        forecast = np.array(forecast)
        # Avoid division by zero
        actual_safe = np.where(actual == 0, 1e-9, actual)
        return float(np.mean(np.abs((actual - forecast) / actual_safe)) * 100)

    @staticmethod
    def get_evaluasi_terbaru():
        return EvaluasiModel.query.filter_by(is_hidden=False).order_by(EvaluasiModel.tanggal_evaluasi.desc()).first()

    @staticmethod
    def tentukan_model_terbaik(mape_sarima, mape_hw):
        if mape_sarima < mape_hw:
            return 'SARIMA'
        return 'Holt-Winters'
