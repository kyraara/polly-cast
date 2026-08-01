"""Entry point untuk cPanel "Setup Python App" (Phusion Passenger).

Passenger mengimpor file ini dan mencari objek bernama `application`.
Taruh file ini di Application Root yang didaftarkan di cPanel.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv

dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app

application = create_app()
