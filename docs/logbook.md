# Logbook Perubahan — 20 Juli 2026

## 1. Perbaikan Tabel Proyeksi PDF (Header Terpotong Halaman)
**File:** `app/services/report_service.py`
- `repeatRows=1` ditambahkan pada konstruktor `Table()` tabel proyeksi agar header kolom muncul kembali di setiap halaman ketika tabel terpotong oleh page break

## 2. Hapus "Rekomendasi Model Terbaik" dari Info Block PDF
**File:** `app/services/report_service.py`
- Baris "Rekomendasi Model Terbaik" dihapus dari tabel meta info bawah kop surat karena sudah diwakili oleh Section 1 (Tabel Metrik Evaluasi)

## 3. Perbaikan Signature Block PDF
**File:** `app/services/report_service.py`
- Teks "Dicetak oleh: ..." dihapus
- Jabatan dinamis: "Kepala Bagian Operasional" (`kabag_operasional`) / "Manager" (`manager`)
- Baris username dihapus (cukup jabatan)
- Margin dokumen diubah dari 40pt ke 2 cm
- Garis bawah (`<u>`) pada username dihapus
- Metadata PDF: `author=username`, `title="Laporan Hasil Peramalan Distribusi LPG"`

## 4. Validasi Import Excel — Minimal 12 Bulan
**File:** `app/services/distribusi_service.py`
- `validasi_format_data()` sekarang mengecek jumlah bulan unik dalam file yang diupload
- Jika kurang dari 12 bulan, raise `ValueError` dengan pesan penolakan

## 5. Menu Baru — Riwayat Peramalan (untuk Manager)
**File Baru:** `app/blueprints/riwayat/__init__.py`
- Blueprint `riwayat_bp` dengan nama `'riwayat'`

**File Baru:** `app/blueprints/riwayat/routes.py`
- Route `GET /riwayat` dengan `@role_required('manager')`
- Mengambil semua `EvaluasiModel` diurutkan `tanggal_evaluasi DESC`
- Menampilkan tabel: Tanggal Eksekusi, Tahun Proyeksi, MAPE SARIMA, MAPE HW, Total Proyeksi, Aksi (Unduh PDF)
- Angka MAPE model terbaik ditampilkan dengan warna merah bold

**File Baru:** `app/templates/riwayat/index.html`
- Template tabel riwayat dengan pewarnaan merah pada MAPE model terbaik

**File Modifikasi:** `app/__init__.py`
- Registrasi `riwayat_bp`

**File Modifikasi:** `app/templates/base.html`
- Menu "Riwayat Peramalan" di sidebar, hanya tampil untuk role `manager`

**File Modifikasi:** `app/blueprints/evaluasi/routes.py`
- `export_pdf()` sekarang menerima parameter query `?id_evaluasi=`
- Menambahkan import `request` dan `EvaluasiModel`

## 6. Tampilan Riwayat Peramalan — Samakan dengan Hasil & Evaluasi
**File:** `app/templates/riwayat/index.html`
- `page-greeter` / `page-title` / `page-subtitle` menggantikan header sederhana
- Kartu menggunakan `border-radius:16px`, `shadow-sm`, `var(--border-card)`
- Header kartu `bg-white px-4 pt-4 pb-2 border-0` dengan `fw-700`
- Warna teks konsisten (`var(--text-primary)`, `var(--text-muted)`)
- Angka menggunakan `font-monospace`

## 7. Pagination Server-Side — Riwayat Peramalan
**File:** `app/blueprints/riwayat/routes.py`
- Import `request`, parameter `page` dari query string
- Ganti `.all()` dengan `.paginate(page=page, per_page=10, error_out=False)`
- Objek `pagination` dikirim ke template

**File:** `app/templates/riwayat/index.html`
- Nomor urut absolut: `(pagination.page - 1) * 10 + loop.index`
- Pagination bar muncul jika `pagination.pages > 1`
- Info "Menampilkan X-Y dari Z data"
- Tombol « Sebelumnya / Selanjutnya » (disable di ujung)
- Nomor halaman (window 5 halaman, ellipsis)
- Halaman aktif di-highlight warna `--primary`

## 8. Sembunyikan Data Riwayat Lama (is_hidden)
**File:** `app/models/evaluasi_model.py`
- Tambah kolom `is_hidden = db.Column(db.Boolean, default=False)`

**File:** `app/services/evaluation_service.py`
- `get_evaluasi_terbaru()` filter `.filter_by(is_hidden=False)`

**File:** `app/blueprints/riwayat/routes.py`
- Query riwayat filter `.filter_by(is_hidden=False)`

**Database:**
- Migration: `flask db migrate -m "add is_hidden column"` → `flask db upgrade`
- **166 data lama** di-set `is_hidden = True`

## 9. Petunjuk Import Data Distribusi — Minimal 12 Bulan
**File:** `app/templates/distribusi/index.html`
- Ditambahkan baris "Data yang diimport minimal **12 bulan (1 tahun)**" di alert petunjuk format

## 10. Perbaikan Grafik PDF Riwayat — Filter Historis Sesuai Periode Evaluasi
**File:** `app/services/report_service.py`
- `cutoff = predictions[0].periode_prediksi` untuk membatasi data historis
- `Distribusi.query.filter(Distribusi.periode_tanggal < cutoff)` — hanya data sebelum periode prediksi pertama
- Memperbaiki grafik yang aneh (mundur ke belakang) pada riwayat no. 2 & 3 karena data historis penuh (terkini) dicampur dengan prediksi lama

## 11. Ubah Nama File & Subject PDF Riwayat — "Riwayat Peramalan Distribusi LPG (tahun)"
**File:** `app/templates/riwayat/index.html`
- Link unduh PDF ditambah `?source=riwayat`

**File:** `app/blueprints/evaluasi/routes.py`
- Parameter `source` dibaca dari query string
- Filename menjadi `Riwayat Peramalan Distribusi LPG ({tahun}).pdf` jika dari menu riwayat

**File:** `app/services/report_service.py`
- Parameter `source` diteruskan ke `generate_laporan_pdf()`
- Title metadata PDF berubah jadi "Riwayat Peramalan Distribusi LPG ({tahun})"

## 12. Sembunyikan Semua Data Riwayat untuk Pengujian
**Database:**
- 4 data riwayat yang masih tampil di-set `is_hidden = True` via script Python
- Halaman riwayat sekarang kosong (siap untuk data baru)

## 13. Hilangkan Desimal pada Data Distribusi — Edit & Simpan
**File:** `app/models/distribusi.py`
- Kolom `jumlah_distribusi` diubah dari `db.Float` → `db.Integer`

**File:** `app/services/distribusi_service.py`
- Import Excel: `.astype(float)` → `.astype(int)`
- `simpan_ke_database()`: konversi `int()` sebelum simpan
- `update_data()`: konversi `int()` sebelum simpan

**File:** `app/blueprints/distribusi/routes.py`
- Route `edit_data_ajax`: `float()` → `int(float(...))`

**File:** `app/templates/distribusi/index.html`
- Input edit: `step="0.01"` → `step="1"`
- JS popup modal: `value = jumlah` → `value = Math.round(parseFloat(jumlah))`
- JS submit: `parseFloat` → `Math.round(parseFloat(...))`
- JS update table: `minimumFractionDigits` dari 2 → 0
- JS update table: locale `'en-US'` → `'id-ID'` (format angka Indonesia)

**Database:**
- Migration: `flask db migrate -m "change jumlah_distribusi to Integer"` → `flask db upgrade`

## 14. Perbaikan Breadcrumb & Header Halaman Riwayat
**File:** `app/templates/base.html`
- Breadcrumb: tambah kondisi `riwayat.index` → menampilkan "Riwayat Peramalan" (sebelumnya jatuh ke "Sistem")

**File:** `app/templates/riwayat/index.html`
- Hapus teks "Menu ini hanya tersedia untuk Manager"
- Hapus header card (icon jam + "Riwayat Peramalan") — tabel langsung di dalam card

## 15. Card Riwayat Peramalan di Dashboard (Manager)
**File:** `app/blueprints/dashboard/routes.py`
- Import `current_user` dan `EvaluasiModel`
- Query `riwayat_count = EvaluasiModel.query.filter_by(is_hidden=False).count()` (khusus manager)
- Variabel `riwayat_count` dikirim ke template

**File:** `app/templates/dashboard/index.html`
- Card "Rata-rata (Mean)" diganti dengan **Riwayat Peramalan** (icon `clock-history`, badge "Riwayat", warna aksen amber)
- Menampilkan jumlah visible riwayat (sinkron dengan tampilan halaman Riwayat Peramalan)

## 16. Perbaikan Error PDF — Fallback DummyModel/None pada Fitted Values
**File:** `app/services/report_service.py`
- `fitted_sarima` sekarang dicek secara bertahap: `fittedvalues()` → `predict_in_sample()` → `np.zeros(len(train))`
- `fitted_hw` sekarang dicek `None` dan `hasattr` sebelum akses, fallback `np.zeros(len(train))`
- Mencegah crash saat model SARIMA gagal training (mengembalikan `DummyModel`) atau HW gagal (mengembalikan `None`)

## 17. Ubah Kalkulasi Growth Rate — Bandingkan Prediksi vs Data Aktual Tahun Sebelumnya
**File:** `app/blueprints/evaluasi/routes.py`
- `import datetime` ditambahkan
- Growth rate sebelumnya: `((late_3mo_avg - early_3mo_avg) / early_3mo_avg) * 100` (membandingkan 3 bulan awal vs 3 bulan akhir dalam proyeksi)
- Growth rate sekarang: `((best_avg - rata_aktual) / rata_ktual) * 100`
- `rata_aktual` = rata-rata data distribusi aktual dari tahun sebelumnya (tahun prediksi - 1)
- `best_avg` = rata-rata hasil prediksi dari model terbaik
- Trend: `meningkat` jika growth_rate > 1%, `menurun` jika < -1%, `stabil` sisanya

**File:** `app/services/report_service.py`
- Perubahan kalkulasi growth rate yang sama untuk PDF

**File:** `app/services/narrative_service.py`
- Parameter baru `tahun_sebelumnya: int = None`
- Narasi diubah dari: *"...dari awal hingga akhir periode proyeksi"*
- Menjadi: *"...dibandingkan tahun sebelumnya ({tahun_sebelumnya})"*

---

# Logbook Perubahan — 31 Juli 2026

## 18. Route Baru — `/evaluasi/compare` (JSON API untuk Grafik Perbandingan)
**File:** `app/blueprints/evaluasi/routes.py`
- Endpoint `GET /evaluasi/compare` mengembalikan JSON payload untuk grafik perbandingan di halaman evaluasi
- Jalur utama: memanggil `ForecastService.run_forecast(id_user, n_periods_ahead=12, save_to_db=False)` untuk data prediksi penuh (historis, test, future)
- Jalur fallback: query langsung ke `Distribusi` dan `Peramalan` jika `run_forecast` gagal
- Response mencakup: `labels_historical`, `values_historical`, `labels_test`, `values_test`, `pred_test_sarima`, `pred_test_hw`, `labels_future`, `pred_future_sarima`, `pred_future_hw`, serta metrik evaluasi (MAE, RMSE, MAPE)

## 19. Load Pretrained Model untuk Grafik PDF (Metadata Validation)
**File:** `app/services/report_service.py`
- Blok validasi metadata dan loading pretrained model dari `models/collab/`:
  - Membaca `models_metadata.json` (berisi `dataset_info.count`, `dataset_info.last_date`)
  - Mengecek kecocokan dataset (`is_matching_dataset`) — jika count & last_date cocok, load model dari `.joblib`
  - Jika dataset berbeda, fallback ke training dinamis via `ForecastService.eksekusi_sarima()` dan `eksekusi_holt_winters()`
- `sarima_test_pred` dan `hw_test_pred` digunakan untuk menggambar garis prediksi fase testing pada grafik PDF
- Fungsi helper `calc_metrics_safe()` untuk kalkulasi MAE/RMSE/MAPE training dengan NaN-safe

## 20. Fungsi Narasi Preprocessing/EDA
**File:** `app/services/narrative_service.py`
- Fungsi baru `generate_preprocessing_narrative(stats, values, decomp, boxplot, date_range) -> dict`
- Menghasilkan 3 narasi untuk halaman EDA:
  - `narasi_validasi`: penjelasan pemilihan model SARIMA & HW berdasarkan karakteristik data
  - `narasi_boxplot`: statistik deskriptif, IQR, outlier, skewness
  - `narasi_decomp`: analisis komponen tren, musiman, residual

## 21. Riwayat Routes — Join Detail dengan Peramalan
**File:** `app/blueprints/riwayat/routes.py`
- Import `Peramalan` untuk mengambil prediksi per id_evaluasi
- Loop setiap item evaluasi untuk menghitung `tahun_proyeksi` (dari `predictions[0].periode_prediksi.year`) dan `total_proyeksi` (berdasarkan model terbaik)

## 22. Dashboard Routes — Import pandas
**File:** `app/blueprints/dashboard/routes.py`
- `import pandas as pd` untuk konversi data distribusi ke pandas Series sebelum analisis EDA

## 23. Sembunyikan 4 Data Riwayat yang Masih Tampil (Pengujian)
**Database (MySQL):**
- `UPDATE tbl_evaluasi_model SET is_hidden = 1 WHERE is_hidden = 0`
- **4 data** (ID 179–182) di-set `is_hidden = True`
- Halaman riwayat sekarang kosong (siap untuk data baru)

## 24. Perbaikan Error PDF — "descriptor 'date' for 'datetime.datetime' objects doesn't apply to a 'int' object"
**File:** `app/services/report_service.py`
- `from datetime import datetime` → `from datetime import datetime, date`
- `datetime.date(tahun_sebelumnya, ...)` → `date(tahun_sebelumnya, ...)`
- Error terjadi karena `datetime` adalah class (bukan module), sehingga `datetime.date()` tidak bisa dipanggil dengan integer

## 25. Perbaikan Indentasi — Syntax Error setelah Edit
**File:** `app/services/report_service.py`
- Baris 346: indentasi berubah dari 8 spasi jadi 4 spasi saat pengeditan sebelumnya
- Menyebabkan syntax error yang membuat website tidak bisa di-load
- Dikembalikan ke 8 spasi (konsisten dengan blok sekitarnya)
