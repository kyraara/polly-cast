# PollyCast — Sistem Peramalan Distribusi LPG

Aplikasi web peramalan distribusi LPG 3 kg untuk PT Polly Jasa Persada (Indramayu),
menggunakan metode **SARIMA** dan **Holt-Winters Exponential Smoothing**.

## Stack

- Flask 3 + Flask-SQLAlchemy + Flask-Migrate + Flask-Login + Flask-WTF
- MySQL 8 (PyMySQL)
- pmdarima / statsmodels / scikit-learn untuk pemodelan
- matplotlib + reportlab untuk laporan PDF

## Struktur

```
lpg_forecast_app/
├── app/
│   ├── blueprints/     auth, dashboard, distribusi, peramalan, evaluasi, riwayat
│   ├── models/         model SQLAlchemy + artefak model terlatih (models/collab/)
│   ├── services/       logika forecast, evaluasi, EDA, narasi, laporan
│   ├── static/         css, js, img
│   └── templates/
├── migrations/         Alembic
├── tests/
└── wsgi.py             entry point (development & Passenger)
docs/                   PRD, arsitektur, rencana implementasi, logbook
```

## Menjalankan secara lokal

Butuh Python 3.10 dan MySQL yang aktif.

```bash
cd lpg_forecast_app
python -m venv venv
venv/Scripts/python.exe -m pip install -r requirements.txt
```

Salin `.env.example` menjadi `.env`, lalu isi nilainya:

```bash
cp lpg_forecast_app/.env.example lpg_forecast_app/.env
```

Generate `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Siapkan database dan akun awal:

```bash
venv/Scripts/python.exe -m flask --app wsgi db upgrade
```

```bash
SEED_KABAG_PASSWORD=... SEED_MANAGER_PASSWORD=... venv/Scripts/python.exe seed.py
```

Jalankan:

```bash
venv/Scripts/python.exe wsgi.py
```

Aplikasi tersedia di `http://localhost:5000` — halaman login ada di `/login`.

## Peran pengguna

| Username  | Peran                       |
|-----------|-----------------------------|
| `kabag`   | Kepala Bagian Operasional   |
| `manager` | Manager                     |

Password ditentukan saat seeding lewat environment variable, tidak disimpan di repo.

## Deployment

Aplikasi ini butuh runtime Python — tidak bisa dijalankan sebagai file statis di
`public_html`. Di cPanel gunakan **Setup Python App** (Passenger) dengan pengaturan:

| Field                      | Nilai                        |
|----------------------------|------------------------------|
| Application root           | `polly-cast/lpg_forecast_app`|
| Application startup file   | `wsgi.py`                    |
| Application entry point    | `app`                        |

Jangan mengisi startup file dengan `passenger_wsgi.py`. cPanel membuat sendiri
`passenger_wsgi.py` sebagai stub yang memuat startup file; kalau startup file
diisi `passenger_wsgi.py`, stub itu memuat dirinya sendiri dan gagal dengan
`RecursionError`. File `passenger_wsgi.py` di app root dikelola cPanel — jangan
diedit atau dimasukkan ke repo, karena akan ditimpa.

Di server wajib:

- `FLASK_ENV=production` (jangan `development` — debugger Werkzeug mengizinkan eksekusi kode)
- `SECRET_KEY` di-set lewat environment variable
- SSL aktif, karena aplikasi punya form login
- Izin tulis pada `app/models/collab/` untuk menyimpan model hasil pelatihan ulang
