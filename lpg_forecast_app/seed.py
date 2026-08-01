import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app
from app.extensions import db
from app.services.auth_service import AuthService

app = create_app()

with app.app_context():
    db.create_all()
    
    # Password diambil dari environment agar tidak tersimpan di source code
    kabag_pw = os.environ.get('SEED_KABAG_PASSWORD')
    manager_pw = os.environ.get('SEED_MANAGER_PASSWORD')

    if not kabag_pw or not manager_pw:
        raise SystemExit(
            "SEED_KABAG_PASSWORD dan SEED_MANAGER_PASSWORD harus di-set sebelum menjalankan seed.\n"
            "Contoh (PowerShell):\n"
            '  $env:SEED_KABAG_PASSWORD="..."; $env:SEED_MANAGER_PASSWORD="..."; python seed.py'
        )

    # Create default users
    kabag = AuthService.create_user('kabag', kabag_pw, 'kabag_operasional')
    manager = AuthService.create_user('manager', manager_pw, 'manager')

    print("Database initialized and seeded successfully!")
    print("Akun dibuat: 'kabag' (kabag_operasional) dan 'manager' (manager).")
