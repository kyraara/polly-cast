import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_name=None):
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')

    if config_name == 'production' and not os.environ.get('SECRET_KEY'):
        raise RuntimeError(
            'SECRET_KEY wajib di-set lewat environment variable pada mode production.'
        )

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Custom Jinja filter: Indonesian number format
    def fmt_id(value, decimal=0):
        if value is None:
            return '0'
        formatted = f"{value:,.{decimal}f}"
        int_part, _, dec_part = formatted.partition('.')
        int_part = int_part.replace(',', '.')
        if decimal > 0:
            return f"{int_part},{dec_part}"
        return int_part

    app.jinja_env.filters['fmt_id'] = fmt_id

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.distribusi import distribusi_bp
    from app.blueprints.peramalan import peramalan_bp
    from app.blueprints.evaluasi import evaluasi_bp
    from app.blueprints.riwayat import riwayat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(distribusi_bp)
    app.register_blueprint(peramalan_bp)
    app.register_blueprint(evaluasi_bp)
    app.register_blueprint(riwayat_bp)

    return app
