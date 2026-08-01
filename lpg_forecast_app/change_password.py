"""Ganti password akun yang sudah ada.

Pemakaian:
    python change_password.py <username>

Password diminta lewat prompt agar tidak tersimpan di history shell.
"""
import getpass
import os
import sys

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.user import User

if len(sys.argv) != 2:
    raise SystemExit('Pemakaian: python change_password.py <username>')

username = sys.argv[1]

app = create_app()

with app.app_context():
    user = User.query.filter_by(username=username).first()
    if not user:
        raise SystemExit(f"User '{username}' tidak ditemukan.")

    password = getpass.getpass(f"Password baru untuk '{username}': ")
    if len(password) < 8:
        raise SystemExit('Password minimal 8 karakter.')
    if password != getpass.getpass('Ulangi password baru: '):
        raise SystemExit('Password tidak cocok.')

    user.password_hash = generate_password_hash(password)
    db.session.commit()
    print(f"Password untuk '{username}' berhasil diperbarui.")
