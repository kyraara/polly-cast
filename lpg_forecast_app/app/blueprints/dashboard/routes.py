from flask import render_template
from app.blueprints.dashboard import dashboard_bp
from flask_login import login_required, current_user
from app.services.eda_service import EDAService
from app.models.distribusi import Distribusi
from app.models.evaluasi_model import EvaluasiModel
import pandas as pd

@dashboard_bp.route('/dashboard')
@login_required
def index():
    records = Distribusi.query.order_by(Distribusi.periode_tanggal.asc()).all()
    if not records:
        return render_template('dashboard/index.html', empty=True)
        
    dates = [pd.to_datetime(r.periode_tanggal) for r in records]
    values = [r.jumlah_distribusi for r in records]
    series = pd.Series(values, index=dates)
    
    stats = EDAService.get_statistik_deskriptif(series)
    decomp = EDAService.get_decomposition(series)
    boxplot = EDAService.get_boxplot_data(series)
    
    riwayat_count = 0
    if current_user.role == 'manager':
        riwayat_count = EvaluasiModel.query.filter_by(is_hidden=False).count()

    chart_data = {
        'labels': [d.strftime('%Y-%m') for d in dates],
        'values': values,
        'decomp': decomp,
        'boxplot': boxplot
    }
    
    return render_template('dashboard/index.html', empty=False, stats=stats, chart_data=chart_data, riwayat_count=riwayat_count)
