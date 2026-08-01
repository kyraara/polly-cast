import datetime
from flask import render_template, send_file, jsonify, flash, redirect, url_for, request
from app.blueprints.evaluasi import evaluasi_bp
from flask_login import login_required, current_user
from app.services.evaluation_service import EvaluationService
from app.services.report_service import ReportService
from app.services.forecast_service import ForecastService
from app.services.narrative_service import generate_ringkasan_eksekutif, generate_analisis_forecasting
from app.models.peramalan import Peramalan
from app.models.distribusi import Distribusi
from app.models.evaluasi_model import EvaluasiModel

@evaluasi_bp.route('/evaluasi', methods=['GET'])
@login_required
def index():
    eval_run = EvaluationService.get_evaluasi_terbaru()
    if not eval_run:
        return render_template('evaluasi/index.html', empty=True)
        
    predictions = Peramalan.query.filter_by(id_evaluasi=eval_run.id_evaluasi).order_by(Peramalan.periode_prediksi.asc()).all()
    
    formatted_preds = []
    sarima_values = []
    hw_values = []
    for p in predictions:
        formatted_preds.append({
            'periode': p.periode_prediksi.strftime('%Y-%m'),
            'sarima': p.nilai_prediksi_sarima,
            'hw': p.nilai_prediksi_hw
        })
        sarima_values.append(p.nilai_prediksi_sarima)
        hw_values.append(p.nilai_prediksi_hw)

    # ── Insight calculations ──
    n = len(formatted_preds)
    sarima_avg = sum(sarima_values) / n if sarima_values else 0
    hw_avg = sum(hw_values) / n if hw_values else 0
    sarima_total = sum(sarima_values)
    hw_total = sum(hw_values)
    best_avg = sarima_avg if eval_run.model_terbaik == 'SARIMA' else hw_avg
    best_total = sarima_total if eval_run.model_terbaik == 'SARIMA' else hw_total

    # Trend direction: compare forecast average vs previous year actual average
    prediksi_tahun = predictions[0].periode_prediksi.year
    tahun_sebelumnya = prediksi_tahun - 1
    data_aktual_sebelumnya = Distribusi.query.filter(
        Distribusi.periode_tanggal >= datetime.date(tahun_sebelumnya, 1, 1),
        Distribusi.periode_tanggal <= datetime.date(tahun_sebelumnya, 12, 31)
    ).all()
    if data_aktual_sebelumnya:
        rata_aktual = sum(r.jumlah_distribusi for r in data_aktual_sebelumnya) / len(data_aktual_sebelumnya)
    else:
        rata_aktual = 0

    if rata_aktual != 0:
        growth_rate = ((best_avg - rata_aktual) / rata_aktual) * 100
    else:
        growth_rate = 0

    if growth_rate > 1:
        trend = 'meningkat'
    elif growth_rate < -1:
        trend = 'menurun'
    else:
        trend = 'stabil'

    # Peak & low (based on model_terbaik values)
    best_values = sarima_values if eval_run.model_terbaik == 'SARIMA' else hw_values
    peak_idx = best_values.index(max(best_values))
    low_idx = best_values.index(min(best_values))

    # Semester averages
    mid = n // 2
    sem1_avg = sum(sarima_values[:mid]) / mid if mid > 0 else 0
    sem2_avg = sum(sarima_values[mid:mid + mid]) / mid if mid > 0 else 0

    insight = {
        'sarima_avg': sarima_avg,
        'hw_avg': hw_avg,
        'sarima_total': sarima_total,
        'hw_total': hw_total,
        'trend': trend,
        'growth_rate': growth_rate,
        'peak_periode': formatted_preds[peak_idx]['periode'] if formatted_preds else '',
        'peak_value': best_values[peak_idx] if best_values else 0,
        'low_periode': formatted_preds[low_idx]['periode'] if formatted_preds else '',
        'low_value': best_values[low_idx] if best_values else 0,
        'semester1_avg': sem1_avg,
        'semester2_avg': sem2_avg,
        'best_avg': best_avg,
        'best_total': best_total
    }

    best_mape = eval_run.mape_sarima if eval_run.model_terbaik == 'SARIMA' else eval_run.mape_hw
    if best_mape < 10:
        kategori_mape = "Sangat Akurat"
    elif best_mape < 20:
        kategori_mape = "Baik"
    elif best_mape < 50:
        kategori_mape = "Cukup"
    else:
        kategori_mape = "Tidak Akurat"

    narasi_ringkasan = generate_ringkasan_eksekutif(
        model_terbaik=eval_run.model_terbaik,
        best_mape=best_mape,
        kategori_mape=kategori_mape,
        mape_sarima=eval_run.mape_sarima,
        mape_hw=eval_run.mape_hw
    )

    narasi_analisis = generate_analisis_forecasting(
        trend=trend,
        growth_rate=growth_rate,
        peak_value=insight['peak_value'],
        peak_periode=insight['peak_periode'],
        low_value=insight['low_value'],
        low_periode=insight['low_periode'],
        semester1_avg=sem1_avg,
        semester2_avg=sem2_avg,
        tahun_sebelumnya=tahun_sebelumnya
    )

    return render_template('evaluasi/index.html', empty=False, evaluasi=eval_run, predictions=formatted_preds, insight=insight, narasi_ringkasan=narasi_ringkasan, narasi_analisis=narasi_analisis)

@evaluasi_bp.route('/evaluasi/compare', methods=['GET'])
@login_required
def compare():
    eval_run = EvaluationService.get_evaluasi_terbaru()
    if not eval_run:
        return jsonify({'status': 'empty'}), 200
        
    try:
        # Get full forecast payload without modifying database
        payload = ForecastService.run_forecast(eval_run.id_user, n_periods_ahead=12, save_to_db=False)
        
        return jsonify({
            'status': 'success',
            'labels_historical': payload['labels_historical'],
            'values_historical': payload['values_historical'],
            'labels_test': payload['labels_test'],
            'values_test': payload['values_test'],
            'pred_test_sarima': payload['pred_test_sarima'],
            'pred_test_hw': payload['pred_test_hw'],
            'labels_future': payload['labels_future'],
            'pred_future_sarima': payload['pred_future_sarima'],
            'pred_future_hw': payload['pred_future_hw'],
            'metrics': {
                'sarima': {'mae': eval_run.mae_sarima, 'rmse': eval_run.rmse_sarima, 'mape': eval_run.mape_sarima},
                'hw': {'mae': eval_run.mae_hw, 'rmse': eval_run.rmse_hw, 'mape': eval_run.mape_hw},
                'model_terbaik': eval_run.model_terbaik
            }
        })
    except Exception as e:
        # Fallback to simple parameters if payload fails
        records = Distribusi.query.order_by(Distribusi.periode_tanggal.asc()).all()
        dates_hist = [r.periode_tanggal.strftime('%Y-%m') for r in records]
        values_hist = [r.jumlah_distribusi for r in records]
        
        predictions = Peramalan.query.filter_by(id_evaluasi=eval_run.id_evaluasi).order_by(Peramalan.periode_prediksi.asc()).all()
        dates_pred = [p.periode_prediksi.strftime('%Y-%m') for p in predictions]
        values_sarima = [p.nilai_prediksi_sarima for p in predictions]
        values_hw = [p.nilai_prediksi_hw for p in predictions]
        
        return jsonify({
            'status': 'success',
            'labels_historical': dates_hist,
            'values_historical': values_hist,
            'labels_test': [],
            'values_test': [],
            'pred_test_sarima': [],
            'pred_test_hw': [],
            'labels_future': dates_pred,
            'pred_future_sarima': values_sarima,
            'pred_future_hw': values_hw,
            'metrics': {
                'sarima': {'mae': eval_run.mae_sarima, 'rmse': eval_run.rmse_sarima, 'mape': eval_run.mape_sarima},
                'hw': {'mae': eval_run.mae_hw, 'rmse': eval_run.rmse_hw, 'mape': eval_run.mape_hw},
                'model_terbaik': eval_run.model_terbaik
            }
        })

@evaluasi_bp.route('/evaluasi/export-pdf', methods=['GET'])
@login_required
def export_pdf():
    id_evaluasi = request.args.get('id_evaluasi', type=int)
    if id_evaluasi:
        eval_run = EvaluasiModel.query.get(id_evaluasi)
    else:
        eval_run = EvaluationService.get_evaluasi_terbaru()
    if not eval_run:
        flash("Tidak ada hasil evaluasi untuk dicetak.", "warning")
        return redirect(url_for('evaluasi.index'))
        
    try:
        source = request.args.get('source', 'evaluasi')
        pdf_buffer = ReportService.generate_laporan_pdf(eval_run.id_evaluasi, current_user.username, current_user.role, source=source)

        if source == 'riwayat':
            predictions = Peramalan.query.filter_by(id_evaluasi=eval_run.id_evaluasi).order_by(Peramalan.periode_prediksi.asc()).all()
            tahun = predictions[0].periode_prediksi.year if predictions else datetime.now().year
            download_name = f"Riwayat Peramalan Distribusi LPG ({tahun}).pdf"
        else:
            download_name = f"laporan_peramalan_{eval_run.tanggal_evaluasi.strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f"Gagal mencetak laporan: {str(e)}", "danger")
        return redirect(url_for('evaluasi.index'))
