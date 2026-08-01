import io
import os
import joblib
import pandas as pd
import numpy as np
import logging

# Use non-gui background backend for Matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime, date

from app.models.evaluasi_model import EvaluasiModel
from app.models.peramalan import Peramalan
from app.models.distribusi import Distribusi
from app.services.eda_service import EDAService
from app.services.evaluation_service import EvaluationService
from app.services.narrative_service import generate_analisis_forecasting

logger = logging.getLogger(__name__)

class ReportService:
    @staticmethod
    def generate_laporan_pdf(id_evaluasi, username, role, source='evaluasi'):
        # 1. Fetch evaluation run
        eval_run = EvaluasiModel.query.get(id_evaluasi)
        if not eval_run:
            raise ValueError(f"Evaluasi model ID {id_evaluasi} tidak ditemukan.")
            
        # 2. Fetch predictions
        predictions = Peramalan.query.filter_by(id_evaluasi=id_evaluasi).order_by(Peramalan.periode_prediksi.asc()).all()
        
        # 3. Fetch historical records (only up to the first prediction period)
        cutoff = predictions[0].periode_prediksi
        records = Distribusi.query.filter(
            Distribusi.periode_tanggal < cutoff
        ).order_by(Distribusi.periode_tanggal.asc()).all()
        if not records:
            raise ValueError("Tidak ada data distribusi historis untuk membuat laporan.")
            
        values_hist = [r.jumlah_distribusi for r in records]
        dates_hist = [pd.to_datetime(r.periode_tanggal) for r in records]
        series = pd.Series(values_hist, index=dates_hist).resample('MS').first()
        
        train_size = int(len(series) * 0.70)
        train = series.iloc[:train_size]
        test = series.iloc[train_size:]

        # 4. Load models to extract fitted values on training set
        collab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'collab'))
        sarima_path = os.path.join(collab_dir, 'auto_sarima_model.joblib')
        hw_path = os.path.join(collab_dir, 'auto_hwes_model.joblib')
        
        metadata_path = os.path.join(collab_dir, 'models_metadata.json')
        import json
        
        is_matching_dataset = False
        if os.path.exists(sarima_path) and os.path.exists(hw_path) and os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    meta = json.load(f)
                dataset_info = meta.get('dataset_info')
                if dataset_info:
                    if (dataset_info.get('count') == len(series) and 
                        dataset_info.get('last_date') == series.index[-1].strftime('%Y-%m-%d')):
                        is_matching_dataset = True
                else:
                    # Fallback to the original skripsi dataset condition
                    original_match = (
                        len(series) == 72 and 
                        series.index[train_size - 1] == pd.to_datetime('2024-02-01')
                    )
                    if original_match:
                        is_matching_dataset = True
            except Exception as e:
                logger.warning(f"Gagal memproses validasi metadata untuk PDF: {e}")
        
        sarima_model = None
        hw_model = None
        sarima_test_pred = None
        hw_test_pred = None
        
        if is_matching_dataset:
            try:
                sarima_model = joblib.load(sarima_path)
                hw_model = joblib.load(hw_path)
                # Generate test predictions from pre-trained models
                sarima_test_pred_obj = sarima_model.predict(n_periods=len(test))
                hw_test_pred_obj = hw_model.forecast(len(test))
                sarima_test_pred = sarima_test_pred_obj.values if hasattr(sarima_test_pred_obj, 'values') else np.asarray(sarima_test_pred_obj)
                hw_test_pred = hw_test_pred_obj.values if hasattr(hw_test_pred_obj, 'values') else np.asarray(hw_test_pred_obj)
            except Exception as e:
                logger.warning(f"Gagal memuat model collab untuk metrik training PDF: {e}")

        # Fallback to dynamic training if models are not preloaded
        if sarima_model is None or hw_model is None:
            from app.services.forecast_service import ForecastService
            sarima_model, sarima_test_pred = ForecastService.eksekusi_sarima(train, len(test))
            hw_model, hw_test_pred = ForecastService.eksekusi_holt_winters(train, len(test))
            sarima_test_pred = sarima_test_pred.values if hasattr(sarima_test_pred, 'values') else np.asarray(sarima_test_pred)
            hw_test_pred = hw_test_pred.values if hasattr(hw_test_pred, 'values') else np.asarray(hw_test_pred)

        # Extract fitted values — with fallback for DummyModel/None
        if hasattr(sarima_model, 'fittedvalues'):
            fitted_sarima = sarima_model.fittedvalues()
        elif hasattr(sarima_model, 'predict_in_sample'):
            fitted_sarima = sarima_model.predict_in_sample()
        else:
            fitted_sarima = np.zeros(len(train))

        if hw_model is not None and hasattr(hw_model, 'fittedvalues'):
            fitted_hw = hw_model.fittedvalues
        else:
            fitted_hw = np.zeros(len(train))

        # Safe metric calculator dropping NaN values
        def calc_metrics_safe(actual, fitted):
            actual = np.array(actual)
            fitted = np.array(fitted)
            mask = ~np.isnan(actual) & ~np.isnan(fitted)
            actual_c = actual[mask]
            fitted_c = fitted[mask]
            if len(actual_c) == 0:
                return 0.0, 0.0, 0.0
            
            mae = float(np.mean(np.abs(actual_c - fitted_c)))
            rmse = float(np.sqrt(np.mean((actual_c - fitted_c) ** 2)))
            actual_safe = np.where(actual_c == 0, 1e-9, actual_c)
            mape = float(np.mean(np.abs((actual_c - fitted_c) / actual_safe)) * 100)
            return mae, rmse, mape

        # Calculate training metrics
        train_mae_sarima, train_rmse_sarima, train_mape_sarima = calc_metrics_safe(train.values, fitted_sarima)
        train_mae_hw, train_rmse_hw, train_mape_hw = calc_metrics_safe(train.values, fitted_hw)

        # Testing metrics from saved evaluation run
        test_mae_sarima = eval_run.mae_sarima
        test_rmse_sarima = eval_run.rmse_sarima
        test_mape_sarima = eval_run.mape_sarima
        
        test_mae_hw = eval_run.mae_hw
        test_rmse_hw = eval_run.rmse_hw
        test_mape_hw = eval_run.mape_hw

        # 5. Build PDF document
        tahun = predictions[0].periode_prediksi.year
        if source == 'riwayat':
            title = f"Riwayat Peramalan Distribusi LPG ({tahun})"
        else:
            title = "Laporan Hasil Peramalan Distribusi LPG"

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            rightMargin=2*cm, 
            leftMargin=2*cm, 
            topMargin=2*cm, 
            bottomMargin=2*cm,
            author=username,
            title=title
        )
        story = []
        
        styles = getSampleStyleSheet()
        
        # Styles definition
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Heading1'],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#064893'),
            spaceAfter=4,
            alignment=1
        )
        
        subtitle_style = ParagraphStyle(
            name='SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=15,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            name='HeadingStyle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#064893'),
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            name='BodyStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.black
        )

        header_cell_style = ParagraphStyle(
            name='HeaderCellStyle',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=10,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )

        cell_style = ParagraphStyle(
            name='CellStyle',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=10,
            textColor=colors.black
        )

        narrative_style = ParagraphStyle(
            name='NarrativeStyle',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#1e293b'),
            alignment=4
        )
        
        # Indonesian Month Formatter helper
        def format_periode_indo(date_obj):
            months_indo = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }
            return f"{months_indo[date_obj.month]} {date_obj.year}"

        # ── KOP SURAT (HEADER) ──
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'logo_pjp.png'))
        logo_img = ""
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=90, height=61)
            except Exception as img_err:
                logger.warning(f"Gagal memuat logo kop PDF: {img_err}")

        kop_title_style = ParagraphStyle(
            name='KopTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=15,
            textColor=colors.HexColor('#064893'),
            alignment=1
        )
        kop_sub_style = ParagraphStyle(
            name='KopSub',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=10.5,
            textColor=colors.HexColor('#dc2626'),
            alignment=1
        )
        kop_address_style = ParagraphStyle(
            name='KopAddress',
            parent=styles['Normal'],
            fontSize=7.8,
            leading=9.5,
            textColor=colors.HexColor('#475569'),
            alignment=1
        )
        
        kop_text = [
            Paragraph("PT. POLLY JASA PERSADA", kop_title_style),
            Paragraph("STASIUN PENGISIAN DAN PENGANGKUTAN BULK ELPIJI ( SPPBE )", kop_sub_style),
            Paragraph("Jl. Raya Krangkeng Desa Dukuh Jati Kec. Krangkeng Kab. Indramayu", kop_address_style),
            Paragraph("Email : pjp_sppbe_krkg@yahoo.co.id", kop_address_style)
        ]
        
        kop_table_data = [[logo_img, kop_text, ""]]
        kop_table = Table(kop_table_data, colWidths=[100, 362, 70])
        kop_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(kop_table)
        
        # Cop separator line
        line_table = Table([[""]], colWidths=[532], rowHeights=[2])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#064893')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 10))

        # Title
        story.append(Paragraph("LAPORAN HASIL PERAMALAN DISTRIBUSI LPG", title_style))
        story.append(Paragraph("Evaluasi Kuantitatif Pemodelan SARIMA dan Holt-Winters Exponential Smoothing", subtitle_style))
        
        # Meta info block
        date_range_str = f"{format_periode_indo(dates_hist[0])} - {format_periode_indo(predictions[-1].periode_prediksi)}"
        info_data = [
            [Paragraph("<b>Tanggal Cetak:</b>", body_style), Paragraph(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), body_style)],
            [Paragraph("<b>Rentang Periode Laporan:</b>", body_style), Paragraph(date_range_str, body_style)]
        ]
        info_table = Table(info_data, colWidths=[170, 362])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 10))
        
        # Compute insights (mirroring evaluasi/routes.py)
        sarima_values = [p.nilai_prediksi_sarima for p in predictions]
        hw_values = [p.nilai_prediksi_hw for p in predictions]
        n_pred = len(predictions)

        sarima_avg = sum(sarima_values) / n_pred if n_pred else 0
        hw_avg = sum(hw_values) / n_pred if n_pred else 0
        sarima_total = sum(sarima_values)
        hw_total = sum(hw_values)

        # Trend: compare forecast average vs previous year actual average
        best_avg = sarima_avg if eval_run.model_terbaik == 'SARIMA' else hw_avg
        prediksi_tahun = predictions[0].periode_prediksi.year
        tahun_sebelumnya = prediksi_tahun - 1
        data_aktual_sebelumnya = Distribusi.query.filter(
            Distribusi.periode_tanggal >= date(tahun_sebelumnya, 1, 1),
            Distribusi.periode_tanggal <= date(tahun_sebelumnya, 12, 31)
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
            trend = "Meningkat"
            trend_icon = "📈"
        elif growth_rate < -1:
            trend = "Menurun"
            trend_icon = "📉"
        else:
            trend = "Stabil"
            trend_icon = "➡"

        # ── RINGKASAN EKSEKUTIF NARRATIVE ──
        # (dihapus berdasarkan permintaan pengguna)
        
        # 1. Tabel Metrik Error
        story.append(Paragraph("1. Tabel Metrik Evaluasi Akurasi (Fase Training &amp; Testing)", heading_style))
        eval_data = [
            [
                Paragraph("Fase / Model", header_cell_style), 
                Paragraph("MAE (kg)", header_cell_style), 
                Paragraph("RMSE (kg)", header_cell_style), 
                Paragraph("MAPE (%)", header_cell_style)
            ],
            [
                Paragraph("<b>Training — SARIMA (Auto)</b>", cell_style), 
                Paragraph(f"{train_mae_sarima:,.0f}", cell_style), 
                Paragraph(f"{train_rmse_sarima:,.0f}", cell_style), 
                Paragraph(f"{train_mape_sarima:.2f}%", cell_style)
            ],
            [
                Paragraph("<b>Training — Holt-Winters</b>", cell_style), 
                Paragraph(f"{train_mae_hw:,.0f}", cell_style), 
                Paragraph(f"{train_rmse_hw:,.0f}", cell_style), 
                Paragraph(f"{train_mape_hw:.2f}%", cell_style)
            ],
            [
                Paragraph("<b>Testing — SARIMA (Auto)</b>", cell_style), 
                Paragraph(f"{test_mae_sarima:,.0f}", cell_style), 
                Paragraph(f"{test_rmse_sarima:,.0f}", cell_style), 
                Paragraph(f"{test_mape_sarima:.2f}%", cell_style)
            ],
            [
                Paragraph("<b>Testing — Holt-Winters</b>", cell_style), 
                Paragraph(f"{test_mae_hw:,.0f}", cell_style), 
                Paragraph(f"{test_rmse_hw:,.0f}", cell_style), 
                Paragraph(f"{test_mape_hw:.2f}%", cell_style)
            ]
        ]
        
        eval_table = Table(eval_data, colWidths=[152, 120, 130, 130])
        eval_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#064893')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(eval_table)
        
        # Best model winner details
        best_mape = test_mape_sarima if eval_run.model_terbaik == 'SARIMA' else test_mape_hw
        if best_mape < 10:
            kategori_mape = "Sangat Akurat"
            alert_bg = colors.HexColor('#f0fdf4') # Green
            alert_border = colors.HexColor('#16a34a')
            alert_text_color = colors.HexColor('#14532d')
        elif best_mape < 20:
            kategori_mape = "Baik"
            alert_bg = colors.HexColor('#eff6ff') # Blue
            alert_border = colors.HexColor('#064893')
            alert_text_color = colors.HexColor('#1e3a8a')
        elif best_mape < 50:
            kategori_mape = "Cukup"
            alert_bg = colors.HexColor('#fffbeb') # Warning Yellow
            alert_border = colors.HexColor('#d97706')
            alert_text_color = colors.HexColor('#78350f')
        else:
            kategori_mape = "Tidak Akurat"
            alert_bg = colors.HexColor('#fff5f5') # Danger Red
            alert_border = colors.HexColor('#dc2626')
            alert_text_color = colors.HexColor('#7f1d1d')
            
        conclusion_style = ParagraphStyle(
            name='ConclusionText',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=12.5,
            textColor=alert_text_color
        )
        
        story.append(Spacer(1, 8))
        conclusion_text = (
            f"<b>Kesimpulan Model Terbaik:</b> Model <b>{eval_run.model_terbaik}</b> berhasil memenangkan pengujian "
            f"karena memiliki tingkat kesalahan paling minimum pada fase Testing dengan nilai MAPE sebesar <b>{best_mape:.2f}%</b>. "
            f"Akurasi peramalan ini dikategorikan <b>\"{kategori_mape}\"</b>."
        )
        
        conclusion_table = Table([[Paragraph(conclusion_text, conclusion_style)]], colWidths=[532])
        conclusion_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), alert_bg),
            ('BOX', (0,0), (-1,-1), 1, alert_border),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(conclusion_table)
        story.append(Spacer(1, 10))
        
        # ── Data for charting ──
        dates_pred = [pd.to_datetime(p.periode_prediksi) for p in predictions]
        sarima_pred_values = [p.nilai_prediksi_sarima for p in predictions]
        hw_pred_values = [p.nilai_prediksi_hw for p in predictions]

        def _chart_base_style(ax):
            ax.set_xlabel('Periode (Tahun)', fontsize=8, fontweight='bold', color='#334155')
            ax.set_ylabel('Jumlah Distribusi (kg)', fontsize=8, fontweight='bold', color='#334155')
            ax.grid(True, linestyle=':', alpha=0.5, color='#cbd5e1')
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            plt.xticks(rotation=12, fontsize=7.5)
            plt.yticks(fontsize=7.5)
            ax.legend(fontsize=7.5, loc='upper left', framealpha=0.9)
            plt.tight_layout()

        def _save_chart(fig, width=480, height=190):
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            img = Image(buf, width=width, height=height)
            img.hAlign = 'CENTER'
            return img

        # 3. Grafik Visualisasi Hasil Peramalan Model SARIMA
        story.append(Paragraph("2. Grafik Visualisasi Hasil Peramalan Model SARIMA", heading_style))

        fig, ax = plt.subplots(figsize=(7.2, 2.8), dpi=150)
        ax.plot(series.index, series.values, label='Data Aktual', color='#064893', linewidth=1.5, zorder=3)

        if sarima_test_pred is not None and len(sarima_test_pred) > 0:
            test_dates_sarima = [train.index[-1]] + list(test.index)
            test_vals_sarima = [train.values[-1]] + list(sarima_test_pred)
            ax.plot(test_dates_sarima, test_vals_sarima, label='Prediksi SARIMA (Testing)', color='#dc2626', linestyle='--', linewidth=1.2, alpha=0.6, zorder=2)

        future_dates = [series.index[-1]] + dates_pred
        future_sarima = [series.values[-1]] + sarima_pred_values
        ax.plot(future_dates, future_sarima, label='Proyeksi SARIMA', color='#dc2626', linestyle=':', linewidth=2.0, zorder=4)
        ax.axvline(x=test.index[0], color='#f59e0b', linestyle='--', linewidth=0.8, alpha=0.7)
        _chart_base_style(ax)
        story.append(_save_chart(fig))
        story.append(Spacer(1, 10))
        story.append(PageBreak())

        # 3. Grafik Visualisasi Hasil Peramalan Model Holt-Winters
        story.append(Paragraph("3. Grafik Visualisasi Hasil Peramalan Model Holt-Winters", heading_style))

        fig, ax = plt.subplots(figsize=(7.2, 2.8), dpi=150)
        ax.plot(series.index, series.values, label='Data Aktual', color='#064893', linewidth=1.5, zorder=3)

        if hw_test_pred is not None and len(hw_test_pred) > 0:
            test_dates_hw = [train.index[-1]] + list(test.index)
            test_vals_hw = [train.values[-1]] + list(hw_test_pred)
            ax.plot(test_dates_hw, test_vals_hw, label='Prediksi Holt-Winters (Testing)', color='#16a34a', linestyle='--', linewidth=1.2, alpha=0.6, zorder=2)

        future_hw = [series.values[-1]] + hw_pred_values
        ax.plot(future_dates, future_hw, label='Proyeksi Holt-Winters', color='#16a34a', linestyle=':', linewidth=2.0, zorder=4)
        ax.axvline(x=test.index[0], color='#f59e0b', linestyle='--', linewidth=0.8, alpha=0.7)
        _chart_base_style(ax)
        story.append(_save_chart(fig))
        story.append(Spacer(1, 10))

        # 5. Grafik Perbandingan Hasil Prediksi (SARIMA vs Holt-Winters)
        story.append(Paragraph("4. Grafik Perbandingan Hasil Prediksi (SARIMA vs Holt-Winters)", heading_style))

        fig, ax = plt.subplots(figsize=(7.2, 2.8), dpi=150)
        ax.plot(series.index, series.values, label='Data Aktual', color='#064893', linewidth=1.5, zorder=3)
        ax.plot(future_dates, future_sarima, label='Proyeksi SARIMA', color='#dc2626', linestyle=':', linewidth=2.0, zorder=4)
        ax.plot(future_dates, future_hw, label='Proyeksi Holt-Winters', color='#16a34a', linestyle=':', linewidth=2.0, zorder=4)
        ax.axvline(x=series.index[-1], color='#8b5cf6', linestyle=':', linewidth=0.8, alpha=0.7, label='Batas Historis/Peramalan')
        _chart_base_style(ax)
        story.append(_save_chart(fig))
        story.append(Spacer(1, 10))
        
        # 6. Tabel Rincian Prediksi
        story.append(Paragraph("5. Tabel Proyeksi Volume Distribusi LPG (12 Periode Depan)", heading_style))
        
        pred_data = [
            [
                Paragraph("No", header_cell_style),
                Paragraph("Periode", header_cell_style), 
                Paragraph("SARIMA (kg)", header_cell_style), 
                Paragraph("Holt-Winters (kg)", header_cell_style),
                Paragraph("Setara Tabung 3 kg", header_cell_style),
                Paragraph("Setara Metrik Ton (MT)", header_cell_style),
                Paragraph("Est. Refill (15MT)", header_cell_style)
            ]
        ]
        
        for idx, p in enumerate(predictions):
            best_val = p.nilai_prediksi_sarima if eval_run.model_terbaik == 'SARIMA' else p.nilai_prediksi_hw
            tabung_3kg = best_val / 3.0
            metrik_ton = best_val / 1000.0
            est_refill = int((best_val + 14999) // 15000)
            
            pred_data.append([
                Paragraph(str(idx + 1), cell_style),
                Paragraph(f"{p.periode_prediksi.month:02d} - {p.periode_prediksi.year}", cell_style),
                Paragraph(f"{p.nilai_prediksi_sarima:,.0f}", cell_style),
                Paragraph(f"{p.nilai_prediksi_hw:,.0f}", cell_style),
                Paragraph(f"{tabung_3kg:,.0f}", cell_style),
                Paragraph(f"{metrik_ton:,.2f}", cell_style),
                Paragraph(f"{est_refill} kali", cell_style)
            ])
            
        pred_table = Table(pred_data, colWidths=[25, 85, 100, 100, 80, 75, 70], repeatRows=1)
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#064893')),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('ALIGN', (0,1), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(pred_table)
        story.append(Spacer(1, 15))
        
        # ── INSIGHT PANEL ──
        story.append(Spacer(1, 5))
        story.append(Paragraph("6. Analisis Insight Hasil Peramalan", heading_style))
        
        # Peak & low (based on model_terbaik values)
        best_values = sarima_values if eval_run.model_terbaik == 'SARIMA' else hw_values
        peak_idx = best_values.index(max(best_values))
        low_idx = best_values.index(min(best_values))
        
        # Semester averages
        mid = n_pred // 2
        sem1_avg = sum(sarima_values[:mid]) / mid if mid > 0 else 0
        sem2_avg = sum(sarima_values[mid:mid + mid]) / mid if mid > 0 else 0
        
        insight_rows = [
            [Paragraph("<b>Rata-rata SARIMA</b>", cell_style), Paragraph(f"{sarima_avg:,.0f} kg", cell_style)],
            [Paragraph("<b>Rata-rata Holt-Winters</b>", cell_style), Paragraph(f"{hw_avg:,.0f} kg", cell_style)],
            [Paragraph("<b>Total SARIMA (12 bln)</b>", cell_style), Paragraph(f"{sarima_total:,.0f} kg", cell_style)],
            [Paragraph("<b>Total Holt-Winters (12 bln)</b>", cell_style), Paragraph(f"{hw_total:,.0f} kg", cell_style)],
            [Paragraph("<b>Tren Proyeksi</b>", cell_style), Paragraph(f"{trend_icon} {trend}", cell_style)],
            [Paragraph("<b>Pertumbuhan</b>", cell_style), Paragraph(f"{growth_rate:,.1f}%", cell_style)],
            [Paragraph("<b>Rata-rata Semester 1</b>", cell_style), Paragraph(f"{sem1_avg:,.0f} kg", cell_style)],
            [Paragraph("<b>Rata-rata Semester 2</b>", cell_style), Paragraph(f"{sem2_avg:,.0f} kg", cell_style)],
            [Paragraph("<b>Puncak Tertinggi</b>", cell_style), Paragraph(f"{best_values[peak_idx]:,.0f} kg ({format_periode_indo(predictions[peak_idx].periode_prediksi)})", cell_style)],
            [Paragraph("<b>Terendah</b>", cell_style), Paragraph(f"{best_values[low_idx]:,.0f} kg ({format_periode_indo(predictions[low_idx].periode_prediksi)})", cell_style)],
        ]
        insight_table = Table(insight_rows, colWidths=[210, 322])
        insight_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        story.append(insight_table)
        story.append(Spacer(1, 8))

        narasi_analisis_pdf = generate_analisis_forecasting(
            trend=trend.lower(),
            growth_rate=growth_rate,
            peak_value=best_values[peak_idx],
            peak_periode=format_periode_indo(predictions[peak_idx].periode_prediksi),
            low_value=best_values[low_idx],
            low_periode=format_periode_indo(predictions[low_idx].periode_prediksi),
            semester1_avg=sem1_avg,
            semester2_avg=sem2_avg,
            tahun_sebelumnya=tahun_sebelumnya
        )
        story.append(Paragraph(narasi_analisis_pdf, narrative_style))
        story.append(Spacer(1, 10))
        
        # ── TANDA TANGAN (SIGNATURE BLOCK) ──
        jabatan = "Kepala Bagian Operasional" if role == 'kabag_operasional' else "Manager"
        sig_data = [
            [Paragraph("", body_style), Paragraph(f"Indramayu, {datetime.now().strftime('%d %B %Y')}", body_style)],
            [Paragraph("", body_style), Spacer(1, 35)],
            [Paragraph("", body_style), Paragraph(f"{jabatan}", body_style)]
        ]
        sig_table = Table(sig_data, colWidths=[332, 200])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(sig_table)
        
        # Build document
        doc.build(story)
        buffer.seek(0)
        return buffer
