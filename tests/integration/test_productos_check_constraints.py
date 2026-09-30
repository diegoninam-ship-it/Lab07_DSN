import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Producto


def _insertar(app, **campos):
    base = {
        "nombre": "Producto",
        "precio": 10,
        "stock": 1,
        "servidor_origen": "Backend 1 - 8081",
    }
    base.update(campos)
    with app.app_context():
        producto = Producto(**base)
        db.session.add(producto)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_check_nombre_vacio(app):
    _insertar(app, nombre="   ")


def test_check_precio_negativo(app):
    _insertar(app, precio=-1)


def test_check_stock_negativo(app):
    _insertar(app, stock=-1)
