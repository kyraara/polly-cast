import logging
from flask import render_template, jsonify
from app.blueprints.peramalan import peramalan_bp
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.services.forecast_service import ForecastService
from app.services.eda_service import EDAService
from app.services.narrative_service import generate_preprocessing_narrative
from app.models.distribusi import Distribusi
import pandas as pd

logger = logging.getLogger(__name__)

@peramalan_bp.route('/peramalan', methods=['GET'])
@login_required
@role_required('kabag_operasional')
def index():
    return render_template('peramalan/index.html')

@peramalan_bp.route('/peramalan/parameters', methods=['GET'])
@login_required
@role_required('kabag_operasional')
def get_parameters():
    params = ForecastService.get_active_parameters()
    if params:
        return jsonify({
            'status': 'success',
            'data': params
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Parameter model belum tersedia. Silakan jalankan peramalan terlebih dahulu.'
        }), 404

@peramalan_bp.route('/peramalan/preprocessing-data', methods=['GET'])
@login_required
@role_required('kabag_operasional')
def get_preprocessing_data():
    records = Distribusi.query.order_by(Distribusi.periode_tanggal.asc()).all()
    if not records:
        return jsonify({'status': 'error', 'message': 'Belum ada data distribusi'}), 404

    dates = [pd.to_datetime(r.periode_tanggal) for r in records]
    values = [r.jumlah_distribusi for r in records]
    series = pd.Series(values, index=dates)

    stats = EDAService.get_statistik_deskriptif(series)
    decomp = EDAService.get_decomposition(series)
    boxplot = EDAService.get_boxplot_data(series)

    date_range = {
        'start': dates[0].strftime('%Y-%m-%d'),
        'end': dates[-1].strftime('%Y-%m-%d')
    }

    narrative = generate_preprocessing_narrative(stats, values, decomp, boxplot, date_range)

    return jsonify({
        'status': 'success',
        'data': {
            'stats': stats,
            'decomp': decomp,
            'boxplot': boxplot,
            'labels': [d.strftime('%Y-%m') for d in dates],
            'values': values,
            'total_records': len(records),
            'date_range': date_range,
            'narasi_validasi': narrative['narasi_validasi'],
            'narasi_boxplot': narrative['narasi_boxplot'],
            'narasi_decomp': narrative['narasi_decomp']
        }
    })

@peramalan_bp.route('/peramalan/run', methods=['POST'])
@login_required
@role_required('kabag_operasional')
def run():
    try:
        # Run forecast for 12 months ahead
        payload = ForecastService.run_forecast(current_user.id_user, n_periods_ahead=12)
        payload_keys = list(payload.keys())
        logger.info(f"PAYLOAD KEYS: {payload_keys}")
        logger.info(f"Has step_details: {'step_details' in payload}")
        return jsonify({
            'status': 'success',
            'data': payload
        })
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Terjadi kesalahan internal: {str(e)}"
        }), 500
