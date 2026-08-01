from flask import render_template, request
from app.blueprints.riwayat import riwayat_bp
from flask_login import login_required
from app.utils.decorators import role_required
from app.models.evaluasi_model import EvaluasiModel
from app.models.peramalan import Peramalan

@riwayat_bp.route('/riwayat')
@login_required
@role_required('manager')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = EvaluasiModel.query.filter_by(is_hidden=False).order_by(
        EvaluasiModel.tanggal_evaluasi.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    history = []
    for ev in pagination.items:
        predictions = Peramalan.query.filter_by(id_evaluasi=ev.id_evaluasi).order_by(Peramalan.periode_prediksi.asc()).all()
        if not predictions:
            continue

        tahun_proyeksi = predictions[0].periode_prediksi.year

        if ev.model_terbaik == 'SARIMA':
            total = sum(p.nilai_prediksi_sarima for p in predictions)
        else:
            total = sum(p.nilai_prediksi_hw for p in predictions)

        history.append({
            'id_evaluasi': ev.id_evaluasi,
            'tanggal_evaluasi': ev.tanggal_evaluasi,
            'tahun_proyeksi': tahun_proyeksi,
            'model_terbaik': ev.model_terbaik,
            'mape_sarima': ev.mape_sarima,
            'mape_hw': ev.mape_hw,
            'total_proyeksi': total,
        })

    return render_template('riwayat/index.html', history=history, pagination=pagination)
