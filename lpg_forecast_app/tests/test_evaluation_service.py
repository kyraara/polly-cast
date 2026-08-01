from app.services.evaluation_service import EvaluationService

def test_mae():
    actual = [100, 200, 300]
    forecast = [90, 210, 300]
    mae = EvaluationService.hitung_mae(actual, forecast)
    assert round(mae, 2) == 6.67

def test_rmse():
    actual = [100, 200, 300]
    forecast = [90, 210, 300]
    rmse = EvaluationService.hitung_rmse(actual, forecast)
    assert round(rmse, 2) == 8.16

def test_mape():
    actual = [100, 200, 300]
    forecast = [90, 210, 300]
    mape = EvaluationService.hitung_mape(actual, forecast)
    assert round(mape, 2) == 5.0

def test_model_selection():
    assert EvaluationService.tentukan_model_terbaik(5.0, 7.0) == 'SARIMA'
    assert EvaluationService.tentukan_model_terbaik(12.0, 8.5) == 'Holt-Winters'
