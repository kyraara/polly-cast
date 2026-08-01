from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message="Username tidak boleh kosong.")])
    password = PasswordField('Password', validators=[DataRequired(message="Password tidak boleh kosong.")])
    remember = BooleanField('Ingat Saya')
    submit = SubmitField('Masuk')
