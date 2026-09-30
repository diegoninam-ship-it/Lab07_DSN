from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length


class FormularioBase(FlaskForm):
    class Meta:
        locales = ["es"]


class LoginForm(FormularioBase):
    correo = StringField("Correo", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(max=128)])
