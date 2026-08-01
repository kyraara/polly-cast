import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_ringkasan_eksekutif(
    model_terbaik: str,
    best_mape: float,
    kategori_mape: str,
    mape_sarima: float,
    mape_hw: float
) -> str:
    if kategori_mape == "Sangat Akurat":
        kesimpulan = "model dinilai <b>sangat valid</b> dan memiliki presisi prediksi yang sangat baik"
    elif kategori_mape == "Baik":
        kesimpulan = "model dinilai <b>cukup valid</b> dengan tingkat presisi yang memadai"
    elif kategori_mape == "Cukup":
        kesimpulan = "model dinilai <b>cukup memadai</b>, namun perlu pengamatan lebih lanjut pada implementasinya"
    else:
        kesimpulan = "model memiliki tingkat kesalahan yang tinggi, hasil prediksi perlu diinterpretasikan dengan hati-hati"

    narasi = (
        f"Berdasarkan hasil pengujian pada fase testing terhadap dua model, yaitu "
        f"SARIMA (MAPE: <b>{mape_sarima:.2f}%</b>) dan Holt-Winters "
        f"(MAPE: <b>{mape_hw:.2f}%</b>), "
        f"model <b>{model_terbaik}</b> terpilih sebagai model terbaik "
        f"karena memiliki nilai MAPE terendah sebesar <b>{best_mape:.2f}%</b>. "
        f"Nilai tersebut termasuk dalam kategori <b>\"{kategori_mape}\"</b> "
        f"menurut standar kriteria akurasi peramalan time series. "
        f"Dengan tingkat kesalahan yang rendah ini, {kesimpulan} "
        f"untuk memproyeksikan distribusi LPG 12 bulan ke depan."
    )
    return narasi


def generate_analisis_forecasting(
    trend: str,
    growth_rate: float,
    peak_value: float,
    peak_periode: str,
    low_value: float,
    low_periode: str,
    semester1_avg: float,
    semester2_avg: float,
    tahun_sebelumnya: int = None
) -> str:
    if growth_rate > 5:
        tren_detail = f"mengalami peningkatan signifikan sebesar {growth_rate:.1f}%"
    elif growth_rate > 1:
        tren_detail = f"mengalami peningkatan sebesar {growth_rate:.1f}%"
    elif growth_rate < -5:
        tren_detail = f"mengalami penurunan signifikan sebesar {abs(growth_rate):.1f}%"
    elif growth_rate < -1:
        tren_detail = f"mengalami penurunan sebesar {abs(growth_rate):.1f}%"
    else:
        tren_detail = "cenderung stabil"

    peak_tabung = peak_value / 3.0
    low_tabung = low_value / 3.0

    if semester2_avg > semester1_avg and semester1_avg != 0:
        selisih_sem = ((semester2_avg - semester1_avg) / semester1_avg * 100)
        sem_desc = f"lebih tinggi {selisih_sem:.1f}%"
    elif semester2_avg < semester1_avg and semester1_avg != 0:
        selisih_sem = ((semester1_avg - semester2_avg) / semester1_avg * 100)
        sem_desc = f"lebih rendah {selisih_sem:.1f}%"
    else:
        sem_desc = "setara"

    if tahun_sebelumnya:
        ref_text = f"dibandingkan tahun sebelumnya ({tahun_sebelumnya})"
    else:
        ref_text = "dibandingkan tahun sebelumnya"

    narasi = (
        f"Berdasarkan hasil peramalan, distribusi LPG diprediksi {tren_detail} {ref_text}. "
        f"Puncak permintaan tertinggi diprediksi terjadi pada "
        f"<b>{peak_periode}</b> sebesar <b>{peak_value:,.0f} kg</b> "
        f"(setara {peak_tabung:,.0f} tabung 3 kg), "
        f"sedangkan permintaan terendah diprediksi terjadi pada "
        f"<b>{low_periode}</b> sebesar <b>{low_value:,.0f} kg</b> "
        f"(setara {low_tabung:,.0f} tabung 3 kg). "
        f"Rata-rata distribusi pada semester II diperkirakan {sem_desc} "
        f"dibandingkan semester I."
    )
    return narasi


def generate_preprocessing_narrative(stats, values, decomp, boxplot, date_range) -> dict:
    trend_vals = [v for v in decomp.get('trend', []) if v is not None]
    seasonal_vals = [v for v in decomp.get('seasonal', []) if v is not None]
    data_mean = stats.get('mean', 0) or 1

    has_trend = False
    has_seasonal = False
    if trend_vals and len(trend_vals) > 2:
        trend_range = max(trend_vals) - min(trend_vals)
        if trend_range > 0.05 * data_mean:
            has_trend = True
    if seasonal_vals and len(seasonal_vals) > 2:
        seasonal_amp = max(seasonal_vals) - min(seasonal_vals)
        if seasonal_amp > 0.03 * data_mean:
            has_seasonal = True

    if has_trend and has_seasonal:
        pola_desc = "adanya pola tren dan musiman"
    elif has_trend:
        pola_desc = "adanya pola tren"
    elif has_seasonal:
        pola_desc = "adanya pola musiman"
    else:
        pola_desc = "pola data yang ada"

    if has_trend and has_seasonal:
        sarima_desc = "mengandung unsur tren dan musiman melalui proses differencing"
        hw_desc = "level, tren, dan musiman"
    elif has_trend:
        sarima_desc = "mengandung unsur tren melalui proses differencing"
        hw_desc = "level, tren, dan musiman"
    elif has_seasonal:
        sarima_desc = "mengandung unsur musiman melalui proses differencing musiman"
        hw_desc = "level, tren, dan musiman"
    else:
        sarima_desc = "mengandung unsur tren dan musiman melalui proses differencing"
        hw_desc = "level, tren, dan musiman"

    narasi_validasi = (
        f"Berdasarkan karakteristik data yang menunjukkan {pola_desc}, "
        f"sistem menerapkan model <b>SARIMA</b> dan <b>Holt-Winters Exponential Smoothing</b> "
        f"sebagai metode peramalan. Model SARIMA digunakan karena mampu menangani data yang "
        f"{sarima_desc}, sedangkan Holt-Winters Exponential mampu memodelkan komponen "
        f"{hw_desc} secara bersamaan. "
        f"Kedua model tersebut digunakan untuk menghasilkan dan membandingkan hasil "
        f"peramalan distribusi LPG."
    )

    # ── Boxplot narrative ──
    iqr = stats.get('q3', 0) - stats.get('q1', 0)
    iqr_pct = (iqr / data_mean * 100) if data_mean else 0
    if iqr_pct < 20:
        iqr_desc = "sempit, menunjukkan data cenderung berkelompok di sekitar nilai tengah"
    elif iqr_pct < 40:
        iqr_desc = "cukup lebar, menunjukkan variasi data yang moderat"
    else:
        iqr_desc = "lebar, menunjukkan sebaran data yang menyebar jauh dari nilai tengah"

    outlier_count = len(boxplot.get('outliers', []))
    if outlier_count > 0:
        outlier_desc = f"Terdeteksi <b>{outlier_count}</b> outlier pada data historis yang perlu dicermati lebih lanjut."
    else:
        outlier_desc = "Tidak terdeteksi outlier pada data historis."

    skew_val = stats.get('skewness', 0)
    if abs(skew_val) < 0.5:
        skew_desc = "Distribusi data cenderung simetris."
    elif skew_val > 0:
        skew_desc = "Distribusi data menceng ke kanan (positif), dengan ekor kanan lebih panjang."
    else:
        skew_desc = "Distribusi data menceng ke kiri (negatif), dengan ekor kiri lebih panjang."

    narasi_boxplot = (
        f"Distribusi data memiliki rentang dari <b>{stats.get('min', 0):,.0f} kg</b> hingga "
        f"<b>{stats.get('max', 0):,.0f} kg</b> dengan nilai tengah (median) "
        f"<b>{stats.get('median', 0):,.0f} kg</b>. "
        f"Rentang antar kuartil (IQR) sebesar <b>{iqr:,.0f} kg</b> ({iqr_pct:.1f}% dari rata-rata) "
        f"menunjukkan sebaran data yang {iqr_desc}. "
        f"{skew_desc} "
        f"{outlier_desc}"
    )

    # ── Decomposition narrative ──
    if trend_vals and len(trend_vals) > 2:
        early_t = trend_vals[len(trend_vals)//4] if len(trend_vals) > 3 else trend_vals[0]
        late_t = trend_vals[-1]
        trend_diff = ((late_t - early_t) / abs(early_t) * 100) if early_t != 0 else 0
        if trend_diff > 5:
            trend_komponen = f"menunjukkan kenaikan sebesar {trend_diff:.1f}% secara keseluruhan"
        elif trend_diff < -5:
            trend_komponen = f"menunjukkan penurunan sebesar {abs(trend_diff):.1f}% secara keseluruhan"
        else:
            trend_komponen = "cenderung stabil secara keseluruhan"
    else:
        trend_komponen = "tidak dapat diidentifikasi dengan jelas karena keterbatasan data"

    if seasonal_vals and len(seasonal_vals) > 2:
        seasonal_amp = max(seasonal_vals) - min(seasonal_vals)
        seasonal_pct = (seasonal_amp / data_mean * 100) if data_mean else 0
        if seasonal_amp > 0.05 * data_mean:
            seasonal_komponen = f"terlihat cukup jelas dengan amplitudo sekitar {seasonal_pct:.1f}% dari rata-rata data"
        else:
            seasonal_komponen = "kurang terlihat, menunjukkan pola musiman yang lemah"
    else:
        seasonal_komponen = "tidak dapat diidentifikasi"

    resid_vals = [v for v in decomp.get('residual', []) if v is not None]
    if resid_vals and len(resid_vals) > 2:
        resid_std = (np.std(resid_vals) / data_mean * 100) if data_mean else 0
        if resid_std < 5:
            resid_komponen = "rendah, mengindikasikan data cukup stabil dan model dekomposisi mampu menangkap pola dengan baik"
        elif resid_std < 15:
            resid_komponen = "sedang, menunjukkan masih ada sebagian variasi yang belum tertangkap oleh komponen tren dan musiman"
        else:
            resid_komponen = "tinggi, mengindikasikan data memiliki fluktuasi acak yang cukup besar"
    else:
        resid_komponen = "tidak dapat diidentifikasi"

    narasi_decomp = (
        f"Komponen tren {trend_komponen}. "
        f"Pola musiman {seasonal_komponen}. "
        f"Variasi komponen residual tergolong <b>{resid_komponen}</b>."
    )

    return {
        'narasi_validasi': narasi_validasi,
        'narasi_boxplot': narasi_boxplot,
        'narasi_decomp': narasi_decomp
    }
