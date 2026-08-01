from flask import render_template, request, redirect, url_for, flash, jsonify
from app.blueprints.distribusi import distribusi_bp
from flask_login import login_required, current_user
from app.utils.decorators import role_required
from app.utils.validators import allowed_file
from app.services.distribusi_service import DistribusiService

@distribusi_bp.route('/distribusi', methods=['GET'])
@login_required
@role_required('kabag_operasional')
def index():
    data = DistribusiService.get_all_data()
    formatted_data = []
    years_set = set()
    for d in data:
        formatted_data.append({
            'periode': d.periode_tanggal.strftime('%Y-%m'),
            'jumlah': d.jumlah_distribusi
        })
        years_set.add(d.periode_tanggal.strftime('%Y'))
    years = sorted(years_set, reverse=True)
    return render_template('distribusi/index.html', data=formatted_data, years=years)

@distribusi_bp.route('/distribusi/import', methods=['POST'])
@login_required
@role_required('kabag_operasional')
def import_data():
    if 'file' not in request.files:
        flash("Tidak ada file yang diunggah.", "danger")
        return redirect(url_for('distribusi.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash("Tidak ada file yang dipilih.", "danger")
        return redirect(url_for('distribusi.index'))
        
    if file and allowed_file(file.filename):
        try:
            df = DistribusiService.baca_file_excel(file)
            clean_df = DistribusiService.validasi_format_data(df)
            added = DistribusiService.simpan_ke_database(clean_df, current_user.id_user)
            flash(f"Data berhasil diimport. {added} data baru ditambahkan.", "success")
        except ValueError as ve:
            flash(f"Validasi Gagal: {str(ve)}", "danger")
        except Exception as e:
            flash(f"Terjadi kesalahan saat memproses file: {str(e)}", "danger")
    else:
        flash("Format file tidak didukung. Harap unggah file Excel (.xlsx atau .xls).", "danger")
        
    return redirect(url_for('distribusi.index'))

@distribusi_bp.route('/distribusi/delete/<string:periode>', methods=['POST'])
@login_required
@role_required('kabag_operasional')
def delete_data(periode):
    try:
        DistribusiService.delete_data(periode)
        flash(f"Data untuk periode {periode} berhasil dihapus.", "success")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Gagal menghapus data: {str(e)}", "danger")
        
    return redirect(url_for('distribusi.index'))

@distribusi_bp.route('/distribusi/delete-ajax/<string:periode>', methods=['POST'])
@login_required
@role_required('kabag_operasional')
def delete_data_ajax(periode):
    try:
        DistribusiService.delete_data(periode)
        return jsonify({'status': 'success', 'message': f'Data {periode} berhasil dihapus.'})
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Gagal menghapus data: {str(e)}'}), 500

@distribusi_bp.route('/distribusi/edit-ajax/<string:periode>', methods=['POST'])
@login_required
@role_required('kabag_operasional')
def edit_data_ajax(periode):
    try:
        data = request.get_json()
        jumlah_baru = int(float(data.get('jumlah')))
        DistribusiService.update_data(periode, jumlah_baru)
        return jsonify({'status': 'success', 'message': f'Data {periode} berhasil diperbarui.'})
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Gagal memperbarui data: {str(e)}'}), 500

@distribusi_bp.route('/distribusi/delete-year', methods=['POST'])
@login_required
@role_required('kabag_operasional')
def delete_year():
    data = request.get_json()
    tahun = data.get('tahun')
    if not tahun:
        return jsonify({'status': 'error', 'message': 'Tahun tidak disertakan.'}), 400
    try:
        deleted_count = DistribusiService.delete_by_year(tahun)
        return jsonify({'status': 'success', 'message': f'Semua data tahun {tahun} berhasil dihapus ({deleted_count} bulan).'})
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Gagal menghapus data: {str(e)}'}), 500

