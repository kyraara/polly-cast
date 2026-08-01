from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user
from app.models.user import User
from app.extensions import db

class AuthService:
    @staticmethod
    def validate_user(username, password):
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    @staticmethod
    def set_hak_akses(user, remember=False):
        return login_user(user, remember=remember)

    @staticmethod
    def logout_session():
        return logout_user()

    @staticmethod
    def create_user(username, password, role):
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return existing_user
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash, role=role)
        db.session.add(new_user)
        db.session.commit()
        return new_user
