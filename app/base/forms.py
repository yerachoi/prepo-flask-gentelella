from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, PasswordField
from wtforms.validators import DataRequired

## login and registration


class LoginForm(FlaskForm):
    username = TextField('Username', id='username_login')
    password = PasswordField('Password', id='pwd_login')


class CreateAccountForm(FlaskForm):
    username = TextField('Username', id='username_create')
    email = TextField('Email')
    password = PasswordField('Password', id='pwd_create')


class AddUrlForm(FlaskForm):
    # content = TextAreaField('URL', id='url', validators=[DataRequired('URL은 필수입력 항목입니다.')])
    content = TextAreaField('URL', id='url')