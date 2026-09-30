from datetime import datetime, timezone
from decimal import Decimal

from app.models import Producto, Usuario


def test_set_password_no_guarda_texto_plano():
    usuario = Usuario(nombre="Test", correo="test@test.com")
    usuario.set_password("Demo1234!")
    assert usuario.password_hash != "Demo1234!"


def test_check_password_correcta_e_incorrecta():
    usuario = Usuario(nombre="Test", correo="test@test.com")
    usuario.set_password("Demo1234!")
    assert usuario.check_password("Demo1234!") is True
    assert usuario.check_password("otra-clave") is False


def test_producto_to_dict_formato_esperado():
    producto = Producto(
        id=7,
        nombre="Teclado",
        precio=Decimal("12"),
        stock=5,
        servidor_origen="Backend 2 - 8082",
        servidor_actualizacion="Backend 1 - 8081",
        creado_en=datetime(2026, 9, 30, 17, 24, 6, tzinfo=timezone.utc),
        actualizado_en=datetime(2026, 9, 30, 17, 31, 40, tzinfo=timezone.utc),
    )
    datos = producto.to_dict()
    assert datos == {
        "id": 7,
        "nombre": "Teclado",
        "precio": "12.00",
        "stock": 5,
        "servidor_origen": "Backend 2 - 8082",
        "servidor_actualizacion": "Backend 1 - 8081",
        "creado_en": "2026-09-30T17:24:06+00:00",
        "actualizado_en": "2026-09-30T17:31:40+00:00",
    }


def test_producto_to_dict_servidor_actualizacion_nulo():
    producto = Producto(
        id=1,
        nombre="Mouse",
        precio=Decimal("9.5"),
        stock=0,
        servidor_origen="Backend 1 - 8081",
        servidor_actualizacion=None,
        creado_en=datetime(2026, 9, 30, tzinfo=timezone.utc),
        actualizado_en=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )
    datos = producto.to_dict()
    assert datos["servidor_actualizacion"] is None
    assert datos["precio"] == "9.50"
