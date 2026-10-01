from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, PasswordField, StringField
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    StopValidation,
    ValidationError,
)


class FormularioBase(FlaskForm):
    class Meta:
        locales = ["es"]


class LoginForm(FormularioBase):
    correo = StringField("Correo", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(max=128)])


def numero_valido(form, campo):
    """Corta la validación en dos casos: el texto no se pudo convertir (ya hay un
    error de WTForms, evita un segundo mensaje) o Decimal aceptó NaN/Infinity."""
    if campo.data is None:
        raise StopValidation()
    if isinstance(campo.data, Decimal) and not campo.data.is_finite():
        raise StopValidation("Ingresa un número válido.")


class ProductoForm(FormularioBase):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    # InputRequired (no DataRequired): DataRequired rechazaría el valor 0 por ser "falso"
    precio = DecimalField(
        "Precio",
        places=2,
        validators=[InputRequired(), numero_valido, NumberRange(min=0, max=Decimal("99999999.99"))],
    )
    stock = IntegerField(
        "Stock", validators=[InputRequired(), numero_valido, NumberRange(min=0, max=1_000_000)]
    )

    def validate_precio(self, campo):
        if campo.data.as_tuple().exponent < -2:
            raise ValidationError("Máximo 2 decimales.")
