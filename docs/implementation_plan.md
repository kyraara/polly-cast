# Implementation Plan
## Sistem Informasi Peramalan Distribusi LPG
### SPPBE PT Polly Jasa Persada Indramayu

> **Versi:** 1.3 | **Dibuat:** Juni 2026 | **Berdasarkan:** `PRD_Sistem_Peramalan_LPG.md` + `ARCHITECTURE.md`
> **Keputusan Frontend:** Bootstrap 5 (CDN) + Chart.js 4 + custom CSS
> **Keputusan Model:** Auto-ARIMA adaptif (`pmdarima.auto_arima`) — parameter dicari otomatis setiap run. Notasi SARIMA final: `(0,1,0)(0,1,0)₁₂`
> **Keputusan PDF:** ReportLab (murni Python, portabel tanpa GTK runtime)

---

## Ringkasan Tujuan

Membangun sistem web berbasis **Flask** yang mengotomatisasi proses peramalan distribusi LPG bulanan menggunakan model **SARIMA** (via `pmdarima`) dan **Holt-Winters Exponential Smoothing** (via `statsmodels`), dengan fitur manajemen data, visualisasi EDA, evaluasi perbandingan model, dan ekspor laporan PDF. Sistem mengikuti pola arsitektur **BCE (Boundary–Control–Entity)** dan mendukung dua peran pengguna: *Kepala Bagian Operasional* dan *Manager*.

**Keputusan teknis yang sudah ditetapkan:**
| Aspek | Keputusan |
|-------|-----------|
| CSS Framework | **Bootstrap 5.3** (via CDN) |
| Grafik / Chart | **Chart.js 4** (via CDN, data JSON dari Flask) |
| Icon | **Bootstrap Icons 1.x** (via CDN) |
| Custom CSS | `app/static/css/style.css` — override + branding tambahan |
| Template Engine | Jinja2 (bawaan Flask) |
| Model SARIMA | **Auto-ARIMA adaptif** — `pmdarima.auto_arima(seasonal=True, m=12, stepwise=True)`. Notasi final laporan: `(0,1,0)(0,1,0)₁₂` |
| Model Holt-Winters | **Auto-HWES** — tipe additive/multiplicative dipilih otomatis via `EDAService.detect_seasonal_type()` |
| Library Export PDF| **ReportLab** (murni Python, portabel tanpa GTK runtime) |

---

## Keputusan Terpilih

> [!NOTE]
> **✅ Keputusan Model — Auto-ARIMA Adaptif (DITETAPKAN)**
>
> Sistem menggunakan **Auto-ARIMA adaptif** (`pmdarima.auto_arima`) sehingga parameter model dicari secara otomatis setiap kali peramalan dijalankan. Ini membuat sistem lebih fleksibel ketika ada penambahan data baru tanpa intervensi manual.
> Tambahkan catatan kecil di halaman evaluasi bahwa order SARIMA yang ditampilkan (misal: `(p,d,q)(P,D,Q)₁₂`) adalah hasil Auto-ARIMA dan **dapat berbeda** dari analisis manual EViews di laporan.

> [!NOTE]
> **✅ Notasi SARIMA Final (DITETAPKAN)**
>
> Model final yang dilaporkan di Bab IV adalah **SARIMA(0,1,0)(0,1,0)₁₂**. Nilai ini digunakan sebagai acuan pembanding statis di laporan PDF dan keterangan pembanding di halaman evaluasi.

> [!NOTE]
> **✅ Library Export PDF (DITETAPKAN)**
>
> Sistem menggunakan **ReportLab** untuk ekspor PDF karena murni Python dan tidak memerlukan runtime GTK di Windows lokal.

---

## Proposed Changes

### Phase 0 — Setup Proyek & Konfigurasi Awal

#### [NEW] `lpg_forecast_app/` — Root Struktur Proyek

Inisialisasi proyek Flask dengan struktur folder penuh sesuai `ARCHITECTURE.md §4`:

```
lpg_forecast_app/
├── app/
│   ├── __init__.py          ← Application factory (create_app)
│   ├── extensions.py        ← db, login_manager, migrate, csrf
│   ├── config.py            ← DevelopmentConfig, ProductionConfig
│   ├── models/
│   ├── services/
│   ├── blueprints/
│   ├── templates/
│   ├── static/
│   └── utils/
├── migrations/
├── tests/
├── wsgi.py
├── requirements.txt
└── .env
```

#### [NEW] `.env`
```
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=<random-32-byte-hex>
DATABASE_URL=mysql+pymysql://root:password@localhost/lpg_forecast_db
```

#### [NEW] `requirements.txt`
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
reportlab
python-dotenv
```

---

### Phase 1 — Entity Layer (Model Database)

> Mengimplementasikan 4 tabel dari ERD `ARCHITECTURE.md §5`.

#### [NEW] `app/models/user.py` — `tbl_user`

```python
class User(db.Model, UserMixin):
    __tablename__ = 'tbl_user'
    id_user        = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(80), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    role           = db.Column(db.Enum('kabag_operasional', 'manager'), nullable=False)
    # Relasi
    distribusi     = db.relationship('Distribusi', backref='user', lazy=True)
    evaluasi       = db.relationship('EvaluasiModel', backref='user', lazy=True)
```

#### [NEW] `app/models/distribusi.py` — `tbl_distribusi`

```python
class Distribusi(db.Model):
    __tablename__ = 'tbl_distribusi'
    id_distribusi      = db.Column(db.Integer, primary_key=True)
    periode_tanggal    = db.Column(db.Date, nullable=False, unique=True)  # format: YYYY-MM-01
    jumlah_distribusi  = db.Column(db.Float, nullable=False)              # dalam kg
    id_user            = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'))
```

#### [NEW] `app/models/evaluasi_model.py` — `tbl_evaluasi_model`

```python
class EvaluasiModel(db.Model):
    __tablename__ = 'tbl_evaluasi_model'
    id_evaluasi      = db.Column(db.Integer, primary_key=True)
    tanggal_evaluasi = db.Column(db.DateTime, default=datetime.utcnow)
    mae_sarima       = db.Column(db.Float)
    rmse_sarima      = db.Column(db.Float)
    mape_sarima      = db.Column(db.Float)
    mae_hw           = db.Column(db.Float)
    rmse_hw          = db.Column(db.Float)
    mape_hw          = db.Column(db.Float)
    model_terbaik    = db.Column(db.String(20))  # 'SARIMA' atau 'Holt-Winters'
    id_user          = db.Column(db.Integer, db.ForeignKey('tbl_user.id_user'))
    peramalan        = db.relationship('Peramalan', backref='evaluasi', lazy=True)
```

#### [NEW] `app/models/peramalan.py` — `tbl_peramalan`

```python
class Peramalan(db.Model):
    __tablename__ = 'tbl_peramalan'
    id_peramalan          = db.Column(db.Integer, primary_key=True)
    id_evaluasi           = db.Column(db.Integer, db.ForeignKey('tbl_evaluasi_model.id_evaluasi'))
    periode_prediksi      = db.Column(db.Date, nullable=False)
    nilai_prediksi_sarima = db.Column(db.Float)
    nilai_prediksi_hw     = db.Column(db.Float)
```

---

### Phase 2 — Control Layer (Service Layer)

> Semua logic bisnis murni, tidak bergantung pada objek `request` Flask, agar dapat di-unit test secara independen (NFR-07).

#### [NEW] `app/services/auth_service.py` — `AuthService`

| Method | Fungsi | FR Terkait |
|--------|--------|------------|
| `validate_user(username, password)` | Query `tbl_user`, verifikasi hash password | FR-01.1, FR-01.2 |
| `set_hak_akses(user)` | Login Flask-Login, set session | FR-01.3 |
| `logout_session()` | Hapus session via Flask-Login | FR-01.4 |

#### [NEW] `app/services/distribusi_service.py` — `DistribusiService`

| Method | Fungsi | FR Terkait |
|--------|--------|------------|
| `baca_file_excel(file)` | Baca `.xlsx` dengan `pandas.read_excel()` | FR-03.1 |
| `validasi_format_data(df)` | Cek kolom, tipe data, rentang periode | FR-03.2 |
| `simpan_ke_database(df, user_id)` | Bulk insert ke `tbl_distribusi` | FR-03.3 |
| `get_all_data()` | Ambil semua data untuk tampilan daftar | FR-03.4 |
| `delete_data(periode)` | Hapus baris berdasarkan periode tertentu | FR-03.5 |

**Aturan validasi Excel:**
- Kolom wajib: `periode` (YYYY-MM atau MM/YYYY) + `jumlah_distribusi` (numerik > 0)
- Periode tidak boleh duplikat dengan yang sudah ada di DB
- Nilai distribusi harus dalam rentang realistis (>0)

#### [NEW] `app/services/eda_service.py` — `EDAService`

| Method | Fungsi | FR Terkait |
|--------|--------|------------|
| `get_statistik_deskriptif(data)` | Hitung mean, median, min, max, std, skewness, kurtosis | FR-02.3 |
| `get_decomposition(data)` | Dekomposisi deret waktu (tren, musiman, residual) via `statsmodels.seasonal_decompose` | FR-02.5 |
| `get_boxplot_data(data)` | Hitung IQR, outlier untuk boxplot | FR-02.4 |
| `detect_seasonal_type(data)` | Tentukan additive vs multiplicative (untuk Holt-Winters) | FR-04.5 |

Output semua method EDAService dikembalikan sebagai **dict/JSON-serializable** agar langsung dapat di-konsumsi Chart.js.

#### [NEW] `app/services/forecast_service.py` — `ForecastService`

Pipeline utama sesuai Sequence Diagram (`ARCHITECTURE.md §7`):

```python
def run_forecast(user_id, n_periods_ahead=12):
    # 1. Ambil data dari DB
    data = Distribusi.query.order_by(...)
    series = pd.Series(...)

    # 2. Cleaning & transformasi
    series = _cleaning(series)

    # 3. Split 70/30
    train, test = split_data(series)

    # 4. SARIMA
    sarima_model, sarima_forecast_test = eksekusi_sarima(train, test)

    # 5. Holt-Winters
    hw_model, hw_forecast_test = eksekusi_holt_winters(train, test)

    # 6. Evaluasi
    metrics = EvaluationService.hitung_semua_metrik(test, sarima_forecast_test, hw_forecast_test)

    # 7. Simpan ke tbl_evaluasi_model
    evaluasi = _simpan_evaluasi(metrics, user_id)

    # 8. Forecast ke depan
    sarima_future = sarima_model.predict(n_periods=n_periods_ahead)
    hw_future     = hw_model.forecast(n_periods_ahead)

    # 9. Simpan ke tbl_peramalan
    _simpan_peramalan(evaluasi.id_evaluasi, sarima_future, hw_future)

    # 10. Return JSON untuk Chart.js
    return _build_chart_payload(series, test, sarima_forecast_test, hw_forecast_test,
                                 sarima_future, hw_future, metrics)
```

| Method | Fungsi | FR Terkait |
|--------|--------|------------|
| `split_data(series, test_ratio=0.30)` | Bagi 70/30 | FR-04.3 |
| `eksekusi_sarima(train, test, m=12)` | Auto-ARIMA seasonal | FR-04.4 |
| `eksekusi_holt_winters(train, test, m=12)` | ExponentialSmoothing adaptif | FR-04.5 |

#### [NEW] `app/services/evaluation_service.py` — `EvaluationService`

| Method | Formula | FR Terkait |
|--------|---------|------------|
| `hitung_mae(actual, forecast)` | `mean(\|actual - forecast\|)` | FR-04.6 |
| `hitung_rmse(actual, forecast)` | `sqrt(mean((actual - forecast)²))` | FR-04.6 |
| `hitung_mape(actual, forecast)` | `mean(\|actual - forecast\| / actual) × 100` | FR-04.6 |
| `get_evaluasi_terbaru()` | Query evaluasi terakhir dari `tbl_evaluasi_model` | FR-05.1 |
| `tentukan_model_terbaik(mape_sarima, mape_hw)` | Bandingkan MAPE, return nama model | FR-05.4 |

#### [NEW] `app/services/report_service.py` — `ReportService`

| Method | Fungsi | FR Terkait |
|--------|--------|------------|
| `generate_laporan_pdf(id_evaluasi)` | Render data ke PDF menggunakan library ReportLab | FR-06.1, FR-06.2 |

**Konten laporan PDF:**
- Header: nama instansi, tanggal cetak
- Tabel statistik deskriptif
- Tabel evaluasi MAE/RMSE/MAPE kedua model
- Rekomendasi model terbaik
- Tabel prediksi periode mendatang (12 bulan ke depan)
- Grafik perbandingan (embedded sebagai gambar PNG dari matplotlib)

---

### Phase 3 — Boundary Layer (Blueprint Routes + Templates)

#### [NEW] `app/utils/decorators.py`

```python
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

#### [NEW] `app/blueprints/auth/routes.py`

| Route | Method | Akses | Handler |
|-------|--------|-------|---------|
| `/login` | GET | Public | Tampilkan form login |
| `/login` | POST | Public | `AuthService.validate_user()` → redirect by role |
| `/logout` | GET | Login required | `AuthService.logout_session()` |

#### [NEW] `app/blueprints/dashboard/routes.py`

| Route | Method | Akses | Handler |
|-------|--------|-------|---------|
| `/dashboard` | GET | Kabag + Manager | `EDAService.*` → kirim JSON ke template |

Template menampilkan kondisional berdasarkan `current_user.role`:
- **Kedua role:** grafik deret waktu, statistik deskriptif, boxplot, dekomposisi EDA
- Tidak ada perbedaan konten di halaman dashboard (read-only untuk keduanya)

#### [NEW] `app/blueprints/distribusi/routes.py`

| Route | Method | Akses | Handler |
|-------|--------|-------|---------|
| `/distribusi` | GET | Kabag only | Tampilkan daftar data |
| `/distribusi/import` | POST | Kabag only | `DistribusiService.baca_file_excel()` → validasi → simpan |
| `/distribusi/delete/<periode>` | POST | Kabag only | `DistribusiService.delete_data()` |

#### [NEW] `app/blueprints/peramalan/routes.py`

| Route | Method | Akses | Handler |
|-------|--------|-------|---------|
| `/peramalan` | GET | Kabag only | Tampilkan halaman peramalan |
| `/peramalan/run` | POST | Kabag only | `ForecastService.run_forecast()` → return JSON |

> **Catatan implementasi:** Proses `run_forecast()` memakan waktu cukup lama (Auto-ARIMA). Implementasikan dengan **indikator loading** di frontend (spinner + progress text). Pertimbangkan Celery task queue jika proses > 30 detik.

#### [NEW] `app/blueprints/evaluasi/routes.py`

| Route | Method | Akses | Handler |
|-------|--------|-------|---------|
| `/evaluasi` | GET | Kabag + Manager | `EvaluationService.get_evaluasi_terbaru()` |
| `/evaluasi/compare` | GET | Kabag + Manager | Data perbandingan kedua model |
| `/evaluasi/export-pdf` | GET | Kabag + Manager | `ReportService.generate_laporan_pdf()` |

---

### Phase 4 — Frontend (Bootstrap 5 + Chart.js)

> **Stack Frontend yang Ditetapkan:**
> - **Bootstrap 5.3** — layout, komponen UI, form, tabel, modal, badge
> - **Bootstrap Icons 1.x** — ikon navigasi dan tombol aksi
> - **Chart.js 4** — semua visualisasi grafik interaktif
> - **custom `style.css`** — override warna branding, sidebar styling

---

#### [NEW] `app/templates/base.html` — Layout Utama

Komponen Bootstrap yang digunakan:

| Komponen | Penggunaan |
|----------|------------|
| `navbar navbar-expand-lg` | Navigasi atas responsif, collapse ke hamburger di mobile |
| `offcanvas` / `sidebar` | Panel menu samping untuk navigasi antar halaman |
| `alert alert-success/danger/warning` | Flash messages dari Flask |
| `container-fluid` | Wrapper konten utama full-width |
| `dropdown` | Menu profil pengguna (logout) di navbar kanan |

```html
<!-- CDN yang di-load di base.html -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
```

**Struktur layout:**
```
┌─────────────────────────────────────────┐
│  NAVBAR (logo + nav links + user badge) │
├──────────┬──────────────────────────────┤
│ SIDEBAR  │  MAIN CONTENT               │
│ (nav     │  {% block content %}         │
│  links   │  {% endblock %}              │
│  per     │                              │
│  role)   │                              │
└──────────┴──────────────────────────────┘
│  FOOTER (nama sistem + versi)           │
└─────────────────────────────────────────┘
```

- Sidebar menampilkan menu berbeda berdasarkan `current_user.role` (Jinja2 conditional)
- Link aktif diberi class `active` menggunakan `request.endpoint`

---

#### [NEW] `app/templates/auth/login.html` — Halaman Login

| Komponen Bootstrap | Penggunaan |
|-------------------|------------|
| `card` + `card-body` | Container form login terpusat |
| `form-control` | Input username dan password |
| `btn btn-primary` | Tombol submit login |
| `alert alert-danger` | Pesan error jika login gagal |
| `form-floating` | Label mengambang di dalam input field |

**Layout:** Form login di tengah halaman dengan `d-flex justify-content-center align-items-center vh-100`, background gradient custom via `style.css`.

---

#### [NEW] `app/templates/dashboard/index.html` — Dashboard EDA

| Komponen Bootstrap | Penggunaan |
|-------------------|------------|
| `row` + `col-md-*` | Grid layout untuk card statistik dan grafik |
| `card` + `card-header` | Container setiap visualisasi / panel statistik |
| `badge bg-info` | Label satuan data (kg) pada statistik |
| `table table-striped table-hover` | Tabel statistik deskriptif |
| `nav nav-tabs` | Tab untuk beralih antar grafik (time series / decomposition / boxplot) |
| `tab-content` + `tab-pane` | Konten per tab grafik |

**Tata letak:**
```
Row 1: [Kartu Stat: Mean] [Kartu Stat: Min] [Kartu Stat: Max] [Kartu Stat: Std]
Row 2: [Grafik Deret Waktu — col-12]
Row 3: [Boxplot — col-md-5] [Statistik Deskriptif Tabel — col-md-7]
Row 4: [Dekomposisi: Tren] [Musiman] [Residual] — 3 x col-md-4
```

**Chart.js — Grafik Dashboard:**
```javascript
// charts.js
function renderTimeSeriesChart(canvasId, labels, actual) { /* Line chart biru */ }
function renderBoxplot(canvasId, q1, median, q3, min, max, outliers) { /* Boxplot custom */ }
function renderDecomposition(trendId, seasonalId, residualId, data) { /* 3 Line charts */ }
```

---

#### [NEW] `app/templates/distribusi/index.html` — Kelola Data Distribusi

| Komponen Bootstrap | Penggunaan |
|-------------------|------------|
| `card` | Container form upload + tabel data |
| `form-control` `type="file"` | Input file Excel |
| `btn btn-success` `<i class="bi bi-upload">` | Tombol import data |
| `table table-bordered table-striped` | Daftar data distribusi per periode |
| `pagination` | Navigasi halaman tabel (jika data > 20 baris) |
| `modal` | Dialog konfirmasi hapus data |
| `btn btn-danger btn-sm` | Tombol hapus per baris |
| `progress` | Progress bar saat upload file |
| `badge bg-success` / `bg-danger` | Status validasi setelah import |
| `alert` | Notifikasi sukses/gagal import |

**Alur Upload:**
1. Pengguna pilih file `.xlsx`
2. Klik "Import" → loading spinner muncul
3. Flash message Bootstrap (`alert`) tampil di atas tabel:
   - ✅ Hijau: "X baris data berhasil diimport"
   - ❌ Merah: "Format file tidak valid: [pesan error]"

---

#### [NEW] `app/templates/peramalan/index.html` — Proses Peramalan

| Komponen Bootstrap | Penggunaan |
|-------------------|------------|
| `card` | Container tombol dan hasil peramalan |
| `btn btn-primary btn-lg` | Tombol "Mulai Peramalan" |
| `spinner-border` | Loading spinner selama proses Auto-ARIMA + HW |
| `progress` | Progress bar animasi saat proses berjalan |
| `alert alert-info` | Informasi "Proses sedang berjalan..." |
| `nav nav-tabs` | Tab untuk berpindah: SARIMA / Holt-Winters / Perbandingan |
| `badge bg-success` | Label "Selesai" setelah peramalan sukses |

**Alur UX Halaman Peramalan:**
```
[Tombol "Mulai Peramalan"]
    ↓ klik
[Spinner + Progress bar + teks "Memproses Auto-ARIMA..."]
    ↓ selesai (AJAX/fetch)
[Tab SARIMA: Grafik prediksi vs aktual]
[Tab Holt-Winters: Grafik prediksi vs aktual]
[Tab Perbandingan: Kedua model dalam 1 grafik]
```

**Chart.js — Grafik Peramalan:**
```javascript
function renderForecastChart(canvasId, labels, actual, predicted, modelName) {
    // Line chart: actual (biru solid) vs predicted (oranye dashed)
}
function renderForecastComparison(canvasId, labels, actual, sarima, hw) {
    // 3 dataset: actual, SARIMA, Holt-Winters
}
```

---

#### [NEW] `app/templates/evaluasi/index.html` — Hasil & Evaluasi Model

| Komponen Bootstrap | Penggunaan |
|-------------------|------------|
| `card` | Container setiap panel evaluasi |
| `table table-bordered` | Tabel perbandingan MAE/RMSE/MAPE |
| `badge bg-success` / `bg-warning` | Label model terbaik / runner-up |
| `alert alert-success` | Rekomendasi model berdasarkan MAPE terendah |
| `btn btn-danger` `<i class="bi bi-file-pdf">` | Tombol "Unduh Laporan PDF" |
| `accordion` | Lipatan detail parameter model SARIMA dan HW |
| `table table-striped` | Tabel prediksi 12 bulan ke depan |

**Tata letak:**
```
Row 1: [Tabel MAE/RMSE/MAPE — col-md-6] [Alert Rekomendasi Model Terbaik — col-md-6]
Row 2: [Grafik Perbandingan Kedua Model — col-12]
Row 3: [Tabel Prediksi Masa Depan — col-12]
Row 4: [Tombol Unduh PDF — float-end]
```

**Chart.js — Grafik Evaluasi:**
```javascript
function renderComparisonChart(canvasId, labels, actual, sarima, hw) {
    // Line chart 3 dataset dengan warna berbeda
}
function renderMetricsBar(canvasId, sarima_metrics, hw_metrics) {
    // Bar chart grouped: MAE/RMSE/MAPE untuk SARIMA vs HW
}
```

---

#### [NEW] `app/static/css/style.css` — Custom Branding

```css
/* Warna primer sistem (override Bootstrap) */
:root {
  --bs-primary: #1a5276;      /* Biru tua — warna utama */
  --bs-primary-rgb: 26,82,118;
  --sidebar-bg: #1c2833;       /* Sidebar gelap */
  --sidebar-text: #aab7b8;
  --card-border-radius: 0.75rem;
}

/* Sidebar */
.sidebar { background-color: var(--sidebar-bg); min-height: 100vh; width: 240px; }
.sidebar .nav-link { color: var(--sidebar-text); }
.sidebar .nav-link.active { background-color: var(--bs-primary); color: #fff; }

/* Card shadow */
.card { border-radius: var(--card-border-radius); box-shadow: 0 2px 8px rgba(0,0,0,.08); }

/* Login page gradient */
.login-bg { background: linear-gradient(135deg, #1a5276 0%, #2e86c1 100%); }
```

#### [NEW] `app/static/js/charts.js` — Fungsi Chart.js

```javascript
// Palet warna konsisten
const COLORS = {
  actual:   'rgba(41, 128, 185, 1)',    // Biru — data aktual
  sarima:   'rgba(231, 76, 60, 1)',     // Merah — SARIMA
  hw:       'rgba(39, 174, 96, 1)',     // Hijau — Holt-Winters
  trend:    'rgba(142, 68, 173, 1)',    // Ungu — tren
  seasonal: 'rgba(243, 156, 18, 1)',   // Oranye — musiman
  residual: 'rgba(127, 140, 141, 1)',  // Abu — residual
};

// Fungsi-fungsi render
function renderTimeSeriesChart(canvasId, labels, data) { ... }
function renderDecompositionCharts(trendId, seasonalId, residualId, decomp) { ... }
function renderBoxplot(canvasId, stats) { ... }
function renderForecastChart(canvasId, labels, actual, predicted, color) { ... }
function renderForecastComparison(canvasId, labels, actual, sarima, hw) { ... }
function renderComparisonChart(canvasId, labels, actual, sarima, hw) { ... }
function renderMetricsBar(canvasId, sarimaMetrics, hwMetrics) { ... }
```

---

### Phase 5 — Keamanan & RBAC

#### [NEW] `app/utils/decorators.py` + `app/utils/validators.py`

| Komponen | Implementasi |
|----------|--------------|
| CSRF Protection | `Flask-WTF` diaktifkan global di `create_app()` |
| Password Hash | `werkzeug.security.generate_password_hash` + `check_password_hash` |
| Role Guard | Decorator `@role_required('kabag_operasional')` pada semua route sensitif |
| Session | Flask-Login + `@login_required` pada semua blueprint kecuali auth |
| File Validation | `validators.py` → validasi ekstensi `.xlsx` + struktur kolom |

#### Matrix RBAC Lengkap

| Endpoint | Kabag Operasional | Manager |
|----------|:-----------------:|:-------:|
| `GET /login` | ✅ | ✅ |
| `GET /dashboard` | ✅ | ✅ |
| `GET /distribusi` | ✅ | ❌ (403) |
| `POST /distribusi/import` | ✅ | ❌ (403) |
| `POST /distribusi/delete/<periode>` | ✅ | ❌ (403) |
| `GET /peramalan` | ✅ | ❌ (403) |
| `POST /peramalan/run` | ✅ | ❌ (403) |
| `GET /evaluasi` | ✅ | ✅ |
| `GET /evaluasi/compare` | ✅ | ✅ |
| `GET /evaluasi/export-pdf` | ✅ | ✅ |

---

### Phase 6 — Testing

#### [NEW] `tests/test_forecast_service.py`

| Test Case | Skenario |
|-----------|----------|
| `test_split_data_ratio` | Verifikasi split 70/30 dengan 72 data |
| `test_sarima_returns_forecast` | SARIMA menghasilkan array prediksi sepanjang data test |
| `test_holt_winters_returns_forecast` | HW menghasilkan array prediksi sepanjang data test |
| `test_forecast_with_edge_case_data` | Data minimal (< 24 observasi) → raise ValueError |
| `test_run_forecast_saves_to_db` | Pipeline lengkap menyimpan ke DB |

#### [NEW] `tests/test_evaluation_service.py`

| Test Case | Skenario |
|-----------|----------|
| `test_mae_calculation` | MAE = 0 jika actual == forecast |
| `test_rmse_calculation` | RMSE >= MAE selalu |
| `test_mape_calculation` | MAPE dalam persen (misal: ~15.2) |
| `test_model_terbaik_mape_terendah` | Jika MAPE SARIMA < MAPE HW → `model_terbaik = 'SARIMA'` |

---

## Urutan Implementasi (Recommended Sprint)

```mermaid
gantt
    title Sprint Plan — Sistem Peramalan LPG
    dateFormat  YYYY-MM-DD
    section Phase 0 — Setup
    Init proyek, .env, requirements      :p0, 2026-06-23, 1d
    section Phase 1 — Entity
    Models (4 tabel) + Migrasi DB        :p1, after p0, 2d
    Seed data user (kabag + manager)     :p1b, after p1, 1d
    section Phase 2 — Control
    AuthService                          :p2a, after p1b, 1d
    DistribusiService                    :p2b, after p2a, 2d
    EDAService                           :p2c, after p2b, 2d
    ForecastService (SARIMA + HW)        :p2d, after p2c, 3d
    EvaluationService                    :p2e, after p2d, 1d
    ReportService (PDF)                  :p2f, after p2e, 2d
    section Phase 3 — Boundary
    Blueprint routes + decorators        :p3, after p2f, 2d
    section Phase 4 — Frontend
    base.html + login page               :p4a, after p3, 1d
    Dashboard + Chart.js                 :p4b, after p4a, 2d
    Distribusi page                      :p4c, after p4b, 1d
    Peramalan page                       :p4d, after p4c, 1d
    Evaluasi page + PDF download         :p4e, after p4d, 2d
    section Phase 5 — Security
    RBAC + CSRF + validasi file          :p5, after p4e, 1d
    section Phase 6 — Testing
    Unit tests + integrasi               :p6, after p5, 2d
```

---

## Verification Plan

### Automated Tests

```bash
# Jalankan semua unit test
pytest tests/ -v

# Test coverage
pytest tests/ --cov=app/services --cov-report=term-missing
```

### Manual Verification Checklist

| No | Item Verifikasi | Cara Uji |
|----|-----------------|----------|
| 1 | **Login Kabag Ops** — redirect ke dashboard + akses semua menu | Login dengan akun kabag |
| 2 | **Login Manager** — redirect ke dashboard + menu distribusi/peramalan tersembunyi | Login dengan akun manager |
| 3 | **Import Excel** — upload file valid → data masuk DB | Upload `data_lpg.xlsx` |
| 4 | **Import Excel invalid** — pesan error muncul, data tidak masuk DB | Upload file dengan format salah |
| 5 | **Hapus data per periode** — data terhapus dari daftar | Klik tombol hapus |
| 6 | **Proses Peramalan** — spinner muncul, grafik tampil setelah selesai | Klik "Mulai Peramalan" |
| 7 | **Evaluasi** — tabel MAE/RMSE/MAPE tampil, badge model terbaik benar | Buka halaman evaluasi |
| 8 | **Unduh PDF** — file PDF terunduh berisi semua data evaluasi | Klik tombol unduh |
| 9 | **RBAC** — Manager mencoba akses `/distribusi` → HTTP 403 | Test URL langsung |
| 10 | **Logout** — session terhapus, redirect ke login | Klik logout |

### Konsistensi Laporan (Checklist Sidang)

> [!WARNING]
> Selesaikan item berikut sebelum sidang agar tidak ada kontradiksi antara sistem dan laporan:

- [ ] Samakan angka MAE/RMSE/MAPE final antara Tabel 4.10/4.13/4.14 dan narasi setelah Tabel 4.14
- [ ] Putuskan notasi SARIMA final: `(0,1,0)(0,1,0)₁₂` **atau** `(2,1,0)(1,0,0)₁₂` — konsistenkan di semua bab
- [ ] Konfirmasi: sistem pakai Auto-ARIMA adaptif atau parameter statis EViews? Dokumentasikan di Bab IV
- [ ] Hapus komentar draft `[lj1]` dan `[lj2]` dari body teks laporan Word
- [ ] Perbaiki *Error! Bookmark not defined.* (Select All → F9 di Word)
- [ ] Perbaiki penomoran caption salah bab (`Gambar 3.21` → `Gambar 4.21`, dst.)
- [ ] Pastikan `test_forecast_service.py` dan `test_evaluation_service.py` mencakup skenario normal + edge case

---

## Catatan Teknis Penting

### Masalah Performa Auto-ARIMA
`pmdarima.auto_arima` dengan `stepwise=True` dan `seasonal=True, m=12` pada data 72 observasi biasanya memakan waktu **10–60 detik**. Solusi:
- Tampilkan loading spinner di frontend
- Pertimbangkan caching hasil model jika data tidak berubah
- Jika > 30 detik jadi masalah, gunakan **Celery + Redis** untuk background task (opsional untuk scope skripsi)

### Deteksi Additive vs Multiplicative (Holt-Winters)
`EDAService.detect_seasonal_type()` menentukan tipe musiman berdasarkan CV (Coefficient of Variation) amplitudo musiman:
- Jika CV < 0.15 → **Additive**
- Jika CV ≥ 0.15 → **Multiplicative**

### Periode Data ke Format Date
Data Excel kemungkinan berformat `Jan-2020`, `2020-01`, atau `01/2020`. Normalisasi di `DistribusiService.validasi_format_data()` menggunakan `pd.to_datetime()` dengan parameter `format` yang fleksibel, kemudian simpan sebagai `YYYY-MM-01` di database.
