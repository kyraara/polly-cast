import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-12345')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///lpg_forecast.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Shared hosting memutus koneksi MySQL yang menganggur, sementara proses
    # Passenger tetap hidup dan menyimpan koneksi itu di pool. Tanpa ini,
    # request pertama setelah jeda gagal dengan "MySQL server has gone away".
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }

class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
