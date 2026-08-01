from flask import render_template, redirect, url_for, flash, request
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.services.auth_service import AuthService
from flask_login import current_user

@auth_bp.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.validate_user(form.username.data, form.password.data)
        if user:
            AuthService.set_hak_akses(user, remember=form.remember.data)
            flash(f"Selamat datang kembali, {user.username}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash("Username atau password salah.", "danger")
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    AuthService.logout_session()
    flash("Anda telah berhasil logout.", "success")
    return redirect(url_for('auth.login'))
