# Product Requirements Document (PRD)
## Sistem Informasi Peramalan Distribusi LPG
### SPPBE PT Polly Jasa Persada Indramayu

> **Versi:** 1.0  
> **Tanggal:** Juni 2026  
> **Penulis:** Laeli Jamilah (20221030025)  
> **Status:** Draft — Sinkron dengan `ARCHITECTURE.md` dan Laporan Skripsi Bab I–IV

---

## 1. Ringkasan Produk

### 1.1 Latar Belakang

SPPBE PT Polly Jasa Persada Indramayu menghadapi permasalahan ketidaktepatan perencanaan volume distribusi LPG yang menyebabkan terjadinya *overstock* maupun *stockout*, mengganggu stabilitas pasokan ke agen resmi. Kondisi ini dipicu oleh sifat data distribusi LPG yang bersifat dinamis dengan pola tren meningkat dan musiman periodik bulanan, sehingga membutuhkan metode peramalan kuantitatif yang tepat.

Sistem ini dibangun untuk mengotomatisasi proses peramalan distribusi LPG menggunakan dua model *time series* — **SARIMA** dan **Holt-Winters Exponential Smoothing** — serta menyajikan evaluasi perbandingan performa model secara visual agar dapat digunakan sebagai dasar pengambilan keputusan operasional.

### 1.2 Tujuan Produk

| No | Tujuan |
|----|--------|
| 1 | Menganalisis pola tren dan musiman data historis distribusi LPG 2020–2025 (72 observasi) melalui EDA (Exploratory Data Analysis) |
| 2 | Membandingkan akurasi prediksi model SARIMA dan Holt-Winters Exponential Smoothing menggunakan metrik MAE, RMSE, dan MAPE |
| 3 | Membangun sistem informasi peramalan berbasis web yang adaptif dan terotomatisasi untuk mendukung perencanaan distribusi LPG |

### 1.3 Ruang Lingkup

- **In scope:** Distribusi LPG dari SPPBE ke agen resmi Pertamina; data agregasi bulanan; peramalan univariat (jumlah distribusi dalam kg); dua model peramalan (SARIMA & Holt-Winters); ekspor laporan PDF.
- **Out of scope:** Distribusi ke tingkat pangkalan atau konsumen akhir; peramalan per-agen; integrasi real-time dengan sistem Pertamina.

---

## 2. Pengguna & Aktor

Sistem memiliki dua aktor dengan hak akses berbeda sesuai Use Case Diagram (Gambar 4.21–4.22 pada laporan):

| Aktor | Peran | Deskripsi Akses |
|-------|-------|-----------------|
| **Kepala Bagian Operasional** | Operator Utama | Hak akses penuh: mengelola data distribusi (import/hapus), mengeksekusi proses peramalan, melihat hasil evaluasi akurasi, dan mencetak laporan |
| **Manager** | *Decision Maker* | Hak akses pemantauan: melihat dashboard & visualisasi EDA, meninjau hasil perbandingan model, dan mencetak laporan — **tanpa** akses pengelolaan data dan eksekusi peramalan |

---

## 3. Kebutuhan Fungsional

Kebutuhan fungsional disusun berdasarkan peran pengguna (Bab IV.2.3 laporan) dan dipetakan ke endpoint serta service dalam `ARCHITECTURE.md` §6.

### FR-01 — Autentikasi & Manajemen Sesi

| ID | Kebutuhan | Aktor | Route (ARCHITECTURE.md) | Service |
|----|-----------|-------|--------------------------|---------|
| FR-01.1 | Sistem mengelola hak akses setiap pengguna sehingga aktor dapat login sesuai tugasnya | Kabag Ops, Manager | `POST /login` | `AuthService.validate_user()` |
| FR-01.2 | Sistem memvalidasi kombinasi username dan password ke database `tbl_user` | Kabag Ops, Manager | `POST /login` | `AuthService.validate_user()` |
| FR-01.3 | Setelah autentikasi berhasil, sistem menetapkan role dan mengarahkan ke halaman yang sesuai | Kabag Ops, Manager | `POST /login` | `AuthService.set_hak_akses()` |
| FR-01.4 | Sistem menyediakan fitur logout untuk mengakhiri sesi | Kabag Ops, Manager | `GET /logout` | `AuthService.logout_session()` |
| FR-01.5 | Sistem menerapkan pembatasan akses berbasis role (RBAC) sehingga Manager tidak dapat mengakses fitur kelola data dan eksekusi peramalan | Sistem | Semua route | `@role_required` decorator |

### FR-02 — Dashboard & EDA

| ID | Kebutuhan | Aktor | Route | Service |
|----|-----------|-------|-------|---------|
| FR-02.1 | Sistem menampilkan dashboard dengan visualisasi EDA data distribusi LPG historis | Kabag Ops, Manager | `GET /dashboard` | `EDAService.get_decomposition()` |
| FR-02.2 | Dashboard menampilkan grafik deret waktu data aktual distribusi LPG 2020–2025 | Kabag Ops, Manager | `GET /dashboard` | `EDAService` |
| FR-02.3 | Dashboard menampilkan statistik deskriptif (mean, median, min, max, std. dev., skewness, kurtosis) | Kabag Ops, Manager | `GET /dashboard` | `EDAService.get_statistik_deskriptif()` |
| FR-02.4 | Dashboard menampilkan grafik boxplot untuk deteksi outlier | Kabag Ops, Manager | `GET /dashboard` | `EDAService` |
| FR-02.5 | Dashboard menampilkan grafik dekomposisi EDA (tren, musiman, residual) | Kabag Ops, Manager | `GET /dashboard` | `EDAService.get_decomposition()` |

### FR-03 — Kelola Data Distribusi

| ID | Kebutuhan | Aktor | Route | Service |
|----|-----------|-------|-------|---------|
| FR-03.1 | Kepala Bagian Operasional dapat mengunggah data historis distribusi LPG dari file Excel untuk disimpan di database | Kabag Ops | `POST /distribusi/import` | `DistribusiService.baca_file_excel()` |
| FR-03.2 | Sistem memvalidasi format dan struktur file Excel sebelum proses penyimpanan | Kabag Ops | `POST /distribusi/import` | `DistribusiService.validasi_format_data()` |
| FR-03.3 | Sistem menyimpan data yang valid ke `tbl_distribusi` dan menampilkan notifikasi konfirmasi | Kabag Ops | `POST /distribusi/import` | `DistribusiService.simpan_ke_database()` |
| FR-03.4 | Kepala Bagian Operasional dapat melihat daftar data distribusi yang telah diinput per periode | Kabag Ops | `GET /distribusi` | `DistribusiService` |
| FR-03.5 | Kepala Bagian Operasional dapat menghapus data historis pada periode tertentu untuk kemudian diunggah kembali dengan data yang benar | Kabag Ops | `POST /distribusi/delete/<periode>` | `DistribusiService.delete_data()` |

### FR-04 — Proses Peramalan

| ID | Kebutuhan | Aktor | Route | Service |
|----|-----------|-------|-------|---------|
| FR-04.1 | Kepala Bagian Operasional dapat menjalankan proses peramalan distribusi untuk periode selanjutnya | Kabag Ops | `POST /peramalan/run` | `ForecastService.run_forecast()` |
| FR-04.2 | Sistem melakukan *cleaning* dan transformasi data sebelum pemodelan | Sistem | `POST /peramalan/run` | `ForecastService` |
| FR-04.3 | Sistem membagi data dengan rasio **70% training / 30% testing** sesuai desain penelitian | Sistem | `POST /peramalan/run` | `ForecastService.split_data()` |
| FR-04.4 | Sistem memproses data distribusi menggunakan model **SARIMA** dengan pendekatan Auto-ARIMA adaptif (seasonal=True, m=12) | Sistem | `POST /peramalan/run` | `ForecastService.eksekusi_sarima()` |
| FR-04.5 | Sistem memproses data distribusi menggunakan model **Holt-Winters Exponential Smoothing** (additive/multiplicative, seasonal_periods=12) | Sistem | `POST /peramalan/run` | `ForecastService.eksekusi_holt_winters()` |
| FR-04.6 | Sistem menghitung metrik evaluasi (MAE, RMSE, MAPE) untuk kedua model berdasarkan data testing | Sistem | `POST /peramalan/run` | `EvaluationService` |
| FR-04.7 | Sistem menyimpan hasil prediksi ke `tbl_peramalan` dan hasil evaluasi ke `tbl_evaluasi_model` | Sistem | `POST /peramalan/run` | `ForecastService`, `EvaluationService` |
| FR-04.8 | Sistem menampilkan hasil peramalan dalam bentuk visualisasi grafik interaktif (Chart.js) | Kabag Ops | `POST /peramalan/run` | Route → Chart.js JSON |

### FR-05 — Hasil & Evaluasi Model

| ID | Kebutuhan | Aktor | Route | Service |
|----|-----------|-------|-------|---------|
| FR-05.1 | Sistem menampilkan hasil prediksi SARIMA dan Holt-Winters secara berdampingan | Kabag Ops, Manager | `GET /evaluasi` | `EvaluationService.get_evaluasi_terbaru()` |
| FR-05.2 | Sistem menampilkan tabel nilai evaluasi MAE, RMSE, dan MAPE untuk masing-masing model | Kabag Ops, Manager | `GET /evaluasi` | `EvaluationService` |
| FR-05.3 | Sistem menampilkan grafik perbandingan performa kedua model | Kabag Ops, Manager | `GET /evaluasi/compare` | `ForecastService` + `EvaluationService` |
| FR-05.4 | Sistem menampilkan rekomendasi model terbaik berdasarkan nilai MAPE terendah | Kabag Ops, Manager | `GET /evaluasi` | `EvaluationService` |
| FR-05.5 | Sistem menampilkan hasil peramalan distribusi LPG untuk periode mendatang (2026) dari kedua model | Kabag Ops, Manager | `GET /evaluasi` | `ForecastService` |

### FR-06 — Ekspor Laporan

| ID | Kebutuhan | Aktor | Route | Service |
|----|-----------|-------|-------|---------|
| FR-06.1 | Sistem menyediakan fitur ekspor/unduh laporan hasil peramalan dalam format PDF | Kabag Ops, Manager | `GET /evaluasi/export-pdf` | `ReportService.generate_laporan_pdf()` |
| FR-06.2 | Laporan PDF memuat data evaluasi model, grafik perbandingan, dan tabel hasil prediksi periode mendatang | Kabag Ops, Manager | `GET /evaluasi/export-pdf` | `ReportService` |

---

## 4. Kebutuhan Non-Fungsional

| ID | Kategori | Kebutuhan |
|----|----------|-----------|
| NFR-01 | **Keamanan** | Password disimpan sebagai hash menggunakan `werkzeug.security.generate_password_hash`; tidak pernah disimpan sebagai plain text |
| NFR-02 | **Keamanan** | Semua form dilindungi CSRF token menggunakan Flask-WTF |
| NFR-03 | **Keamanan** | Akses halaman memerlukan autentikasi (Flask-Login); pengguna tidak terautentikasi diarahkan ke halaman login |
| NFR-04 | **Akses Berbasis Peran** | Endpoint yang bersifat operasional (`/distribusi/*`, `/peramalan/run`) hanya dapat diakses oleh role `kabag_operasional`; akses lain mendapat respons HTTP 403 |
| NFR-05 | **Performa** | Proses peramalan (Auto-ARIMA + Holt-Winters) selesai dalam waktu yang wajar; sistem dapat menampilkan indikator loading selama proses berlangsung |
| NFR-06 | **Keandalan Data** | Sistem memvalidasi format file Excel sebelum import; data dengan format tidak sesuai ditolak disertai pesan error yang jelas |
| NFR-07 | **Maintainability** | Arsitektur BCE (Boundary–Control–Entity) memisahkan logic business di service layer sehingga dapat di-unit test secara independen |
| NFR-08 | **Skalabilitas** | Sistem menggunakan Auto-ARIMA dan Auto-HWES agar model dapat memperbarui parameternya secara mandiri ketika ada penambahan data baru tanpa intervensi manual |
| NFR-09 | **Kompatibilitas** | Antarmuka web diakses melalui browser standar; frontend dibangun dengan Jinja2 + Bootstrap/Tailwind dan Chart.js |
| NFR-10 | **Akurasi Model** | Target MAPE dalam kategori "Baik" (< 20%) untuk model yang digunakan dalam sistem; model terbaik ditentukan berdasarkan nilai MAPE terendah |

---

## 5. Data & Dataset

| Aspek | Detail |
|-------|--------|
| **Sumber data** | Data historis distribusi LPG SPPBE PT Polly Jasa Persada Indramayu |
| **Cakupan periode** | Januari 2020 – Desember 2025 |
| **Jumlah observasi** | 72 data bulanan |
| **Variabel** | Univariat: (1) Periode waktu (bulan/tahun) sebagai indeks, (2) Jumlah distribusi LPG dalam kilogram (kg) |
| **Format input** | File Excel (.xlsx) diunggah melalui antarmuka web |
| **Split rasio** | 70% data training (~50 observasi), 30% data testing (~22 observasi) |
| **Statistik deskriptif** | Mean: 1.084.992 kg; Min: 840.840 kg; Max: 1.320.360 kg; Std. Dev: 121.462,6 kg; Observasi: 72 |

---

## 6. Model Peramalan

### 6.1 Model SARIMA

| Parameter | Nilai |
|-----------|-------|
| Pendekatan sistem | Auto-ARIMA adaptif (`pmdarima.auto_arima`) |
| Konfigurasi | `seasonal=True`, `m=12`, `stepwise=True` |
| Referensi analisis manual (EViews) | SARIMA(0,1,0)(0,1,0)₁₂ dan SARIMA(2,1,0)(1,0,0)₁₂ |
| Periode musiman | 12 bulan |
| Tahapan | Uji stasioneritas (ADF) → Differencing → Identifikasi ACF/PACF → Estimasi parameter → Uji diagnostik (Ljung-Box) → Peramalan |

### 6.2 Model Holt-Winters Exponential Smoothing

| Parameter | Nilai |
|-----------|-------|
| Pendekatan sistem | Auto-HWES adaptif (`statsmodels.ExponentialSmoothing`) |
| Komponen | Level (α), Trend (β/additive), Seasonal (γ) |
| Tipe musiman | Additive (dipilih otomatis berdasarkan `EDAService.get_decomposition()`) |
| Referensi analisis manual (EViews) | α=0,348; β=γ=0 |
| Periode musiman | 12 bulan |

### 6.3 Metrik Evaluasi

| Metrik | Formula | Interpretasi |
|--------|---------|--------------|
| **MAE** | `mean(|actual - forecast|)` | Rata-rata selisih absolut; satuan sama dengan data |
| **RMSE** | `sqrt(mean((actual - forecast)²))` | Sensitif terhadap error besar; penalti outlier lebih besar |
| **MAPE** | `mean(|actual - forecast| / actual) × 100%` | Persentase error; nilai < 10% = Sangat Baik, 10–20% = Baik, 20–50% = Cukup, > 50% = Buruk |

> **Catatan desain:** Model dengan MAPE terendah ditetapkan sebagai `model_terbaik` dan disimpan di kolom `tbl_evaluasi_model.model_terbaik`.

---

## 7. Arsitektur Sistem

Sistem dibangun dengan pendekatan **Boundary–Control–Entity (BCE)** yang dipetakan langsung ke struktur Flask (lihat `ARCHITECTURE.md` §3):

```
Boundary (Jinja2 Templates + Blueprint Routes)
    │
    ▼
Control (Service Layer: app/services/)
    │
    ▼
Entity (SQLAlchemy Models: app/models/)
    │
    ▼
Database (MySQL)
```

### 7.1 Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Web Framework | Flask (Application Factory + Blueprint) |
| ORM / Database | SQLAlchemy + Flask-Migrate (Alembic), MySQL |
| Auth & Session | Flask-Login, Flask-WTF |
| Forecasting | `pmdarima` (Auto-ARIMA/SARIMA), `statsmodels` (Holt-Winters) |
| Evaluasi | `scikit-learn` / perhitungan manual (MAE, RMSE, MAPE) |
| Visualisasi | Chart.js (client-side; data dikirim sebagai JSON dari Flask) |
| Import Data | `pandas` + `openpyxl` |
| Export Laporan | WeasyPrint atau ReportLab |
| Frontend | Jinja2 + Bootstrap/Tailwind |

### 7.2 Skema Database

Empat tabel utama (lihat `ARCHITECTURE.md` §5):

| Tabel | Deskripsi | Relasi |
|-------|-----------|--------|
| `tbl_user` | Data pengguna (username, password_hash, role) | Berelasi ke `tbl_distribusi` dan `tbl_evaluasi_model` |
| `tbl_distribusi` | Data historis distribusi LPG per periode | FK ke `tbl_user` |
| `tbl_evaluasi_model` | Hasil evaluasi (MAE/RMSE/MAPE) per run peramalan | FK ke `tbl_user`; berelasi ke `tbl_peramalan` |
| `tbl_peramalan` | Nilai prediksi SARIMA & Holt-Winters per periode | FK ke `tbl_evaluasi_model` |

---

## 8. Pemetaan Fitur ke Halaman (GUI)

Berdasarkan wireframe dan HIPO diagram (Gambar 4.31–4.39 pada laporan):

### 8.1 Halaman Kepala Bagian Operasional

| Halaman | Fitur Utama | FR Terkait |
|---------|-------------|------------|
| **Login** | Form username & password, validasi kredensial, notifikasi error | FR-01.1, FR-01.2 |
| **Dashboard** | Grafik deret waktu, statistik deskriptif, boxplot, dekomposisi EDA | FR-02.1 – FR-02.5 |
| **Data Distribusi** | Upload file Excel, daftar data per periode, hapus data per periode | FR-03.1 – FR-03.5 |
| **Peramalan** | Tombol mulai peramalan, indikator proses, hasil grafik SARIMA & HW | FR-04.1 – FR-04.8 |
| **Hasil & Evaluasi** | Tabel MAE/RMSE/MAPE, grafik perbandingan, prediksi masa depan, unduh PDF | FR-05.1 – FR-06.2 |

### 8.2 Halaman Manager

| Halaman | Fitur Utama | FR Terkait |
|---------|-------------|------------|
| **Login** | Form username & password (role manager) | FR-01.1, FR-01.2 |
| **Dashboard** | Visualisasi EDA, statistik deskriptif (read-only) | FR-02.1 – FR-02.5 |
| **Hasil & Evaluasi** | Tabel evaluasi, grafik perbandingan, prediksi, unduh PDF | FR-05.1 – FR-06.2 |

---

## 9. Role-Based Access Control (RBAC)

Sesuai `ARCHITECTURE.md` §8 dan Use Case Diagram (Gambar 4.21–4.22):

| Endpoint | Kabag Operasional | Manager |
|----------|:-----------------:|:-------:|
| `GET /dashboard` | ✅ | ✅ |
| `GET /distribusi` | ✅ | ❌ |
| `POST /distribusi/import` | ✅ | ❌ |
| `POST /distribusi/delete/<periode>` | ✅ | ❌ |
| `POST /peramalan/run` | ✅ | ❌ |
| `GET /evaluasi` | ✅ | ✅ |
| `GET /evaluasi/compare` | ✅ | ✅ |
| `GET /evaluasi/export-pdf` | ✅ | ✅ |

---

## 10. Alur Proses Utama (Pipeline Peramalan)

Mengikuti Sequence Diagram Proses Peramalan (Gambar 4.28 pada laporan) dan `ARCHITECTURE.md` §7:

```
1. Kabag Ops menekan tombol "Mulai Peramalan"
       │
2. Sistem mengambil semua data dari tbl_distribusi
       │
3. Cleaning & transformasi data (handling missing, format periode)
       │
4. Split data: 70% training / 30% testing
       │
5a. Auto-ARIMA (seasonal=True, m=12) → Model SARIMA terbaik
5b. ExponentialSmoothing (additive/multiplicative, m=12) → Model Holt-Winters
       │
6. Hitung MAE, RMSE, MAPE untuk data testing (kedua model)
       │
7. INSERT ke tbl_evaluasi_model (termasuk model_terbaik)
       │
8. Forecast n periode ke depan (2026)
       │
9. INSERT ke tbl_peramalan (nilai prediksi SARIMA & HW per bulan)
       │
10. Return JSON → render grafik interaktif Chart.js
```

---

## 11. Validasi & Checklist Konsistensi

Sebelum implementasi final dan sidang, selaraskan hal berikut antara laporan dan sistem (lihat juga `ARCHITECTURE.md` §9):

- [ ] **Angka evaluasi:** Samakan nilai MAE/RMSE/MAPE final (Tabel 4.10/4.13/4.14 vs. narasi setelah Tabel 4.14 — saat ini terdapat perbedaan)
- [ ] **Notasi SARIMA:** Tentukan dan konsistenkan notasi model final — (0,1,0)(0,1,0)₁₂ atau (2,1,0)(1,0,0)₁₂ — jangan dipakai bergantian tanpa penjelasan eksplisit
- [ ] **Auto-tuning vs. parameter statis:** Konfirmasi apakah sistem akhir menggunakan Auto-ARIMA adaptif (untuk skalabilitas) atau mereproduksi parameter statis EViews (untuk validasi akurasi sidang); dokumentasikan keputusan ini secara eksplisit di narasi Bab IV
- [ ] **Draft comments Word:** Hapus atau selesaikan komentar `[lj1]` dan `[lj2]` dari body teks laporan
- [ ] **Cross-reference rusak:** Update field yang menampilkan `Error! Bookmark not defined.` — gunakan Select All → F9 di Word
- [ ] **Penomoran caption:** Perbaiki caption salah bab (contoh: "Gambar 3.21" → "Gambar 4.21", "Gambar 3.30" → "Gambar 4.30")
- [ ] **Unit test:** Pastikan `test_forecast_service.py` dan `test_evaluation_service.py` mencakup skenario normal, data edge case, dan validasi format file Excel

---

## 12. Dependencies Sistem

```
Flask>=3.0
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
Flask-WTF
PyMySQL
pandas
numpy
pmdarima
statsmodels
scikit-learn
openpyxl
WeasyPrint
python-dotenv
```

---

## 13. Referensi

| Dokumen | Keterangan |
|---------|------------|
| `ARCHITECTURE.md` | Dokumen arsitektur teknis — acuan utama implementasi Flask (BCE, struktur folder, ERD, endpoint, service) |
| Laporan Skripsi Bab I | Latar belakang, rumusan masalah, batasan, dan tujuan penelitian |
| Laporan Skripsi Bab II | Metodologi penelitian (Waterfall), spesifikasi perangkat, kerangka berpikir |
| Laporan Skripsi Bab III | Landasan teori: SARIMA, Holt-Winters, MAE/RMSE/MAPE, UML, teknologi |
| Laporan Skripsi Bab IV | Analisis sistem, dataset, pengolahan data, perancangan UML, wireframe, class diagram |
| Peraturan Menteri ESDM No. 28/2021 | Regulasi distribusi LPG 3 kg bersubsidi |
