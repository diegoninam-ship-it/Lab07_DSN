from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Producto, Usuario
from tests.conftest import overrides_de_prueba


def _app_api(**overrides):
    overrides.setdefault("APP_MODE", "api")
    return create_app(overrides_de_prueba(**overrides))


def _crear_usuario(app, correo="demo@lab07.pe"):
    with app.app_context():
        usuario = Usuario(nombre="Usuario Demo", correo=correo)
        usuario.set_password("Demo1234!")
        db.session.add(usuario)
        db.session.commit()
        return usuario.id


def _crear_producto(app, nombre="Producto", precio="10.00", stock=1, servidor_origen="Backend 1 - 8081"):
    with app.app_context():
        producto = Producto(
            nombre=nombre, precio=Decimal(precio), stock=stock, servidor_origen=servidor_origen
        )
        db.session.add(producto)
        db.session.commit()
        return producto.id


def _cliente_con_sesion(app, usuario_id):
    client = app.test_client()
    with client.session_transaction() as sesion:
        sesion["usuario_id"] = usuario_id
    return client


def test_api_test():
    app = _app_api(SERVER_ID="API-1")
    respuesta = app.test_client().get("/api/test")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "API SERVER · API-1"


def test_api_health():
    app = _app_api()
    respuesta = app.test_client().get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "ok"


def test_productos_sin_sesion_401():
    app = _app_api()
    respuesta = app.test_client().get("/api/productos")
    assert respuesta.status_code == 401
    assert respuesta.get_json() == {"error": "No autenticado"}


def test_productos_con_cookie_invalida_401():
    app = _app_api()
    client = _cliente_con_sesion(app, 999999)
    respuesta = client.get("/api/productos")
    assert respuesta.status_code == 401


def test_productos_forma_exacta_del_json():
    app = _app_api(SERVER_ID="API-1")
    usuario_id = _crear_usuario(app)
    _crear_producto(app, nombre="Teclado", precio="12.00", stock=5)
    client = _cliente_con_sesion(app, usuario_id)
    respuesta = client.get("/api/productos")
    datos = respuesta.get_json()

    assert set(datos.keys()) == {"servidor", "total", "pagina", "limite", "productos"}
    assert datos["servidor"] == "API-1"
    assert datos["total"] == 1
    assert datos["pagina"] == 1
    assert datos["limite"] == 50

    producto = datos["productos"][0]
    assert set(producto.keys()) == {
        "id",
        "nombre",
        "precio",
        "stock",
        "servidor_origen",
        "servidor_actualizacion",
        "creado_en",
        "actualizado_en",
    }
    assert producto["precio"] == "12.00"
    assert producto["servidor_actualizacion"] is None


@pytest.mark.parametrize("limite,esperado", [("0", 1), ("999", 200), ("abc", 50), ("100", 100)])
def test_paginacion_limite_acotado(limite, esperado):
    app = _app_api()
    usuario_id = _crear_usuario(app)
    client = _cliente_con_sesion(app, usuario_id)
    respuesta = client.get(f"/api/productos?limite={limite}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["limite"] == esperado


@pytest.mark.parametrize("pagina,esperado", [("0", 1), ("abc", 1), ("99999999", 1_000_000)])
def test_paginacion_pagina_acotada_sin_error_500(pagina, esperado):
    app = _app_api()
    usuario_id = _crear_usuario(app)
    client = _cliente_con_sesion(app, usuario_id)
    respuesta = client.get(f"/api/productos?pagina={pagina}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["pagina"] == esperado


def test_detalle_producto():
    app = _app_api()
    usuario_id = _crear_usuario(app)
    producto_id = _crear_producto(app, nombre="Mouse")
    client = _cliente_con_sesion(app, usuario_id)
    respuesta = client.get(f"/api/productos/{producto_id}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["nombre"] == "Mouse"


def test_detalle_producto_inexistente_404_json():
    app = _app_api()
    usuario_id = _crear_usuario(app)
    client = _cliente_con_sesion(app, usuario_id)
    respuesta = client.get("/api/productos/999999")
    assert respuesta.status_code == 404
    assert respuesta.get_json() == {"error": "Producto no encontrado"}


def test_detalle_producto_id_mayor_a_32_bits_404():
    app = _app_api()
    usuario_id = _crear_usuario(app)
    client = _cliente_con_sesion(app, usuario_id)
    respuesta = client.get("/api/productos/99999999999")
    assert respuesta.status_code == 404


def test_ruta_api_inexistente_404_json():
    app = _app_api()
    respuesta = app.test_client().get("/api/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.get_json() == {"error": "No encontrado"}


def test_metodo_no_permitido_405_json():
    app = _app_api()
    respuesta = app.test_client().post("/api/productos")
    assert respuesta.status_code == 405
    assert respuesta.get_json() == {"error": "Método no permitido"}


@pytest.mark.parametrize("ruta", ["/login", "/logout", "/", "/productos/nuevo"])
def test_rutas_web_no_existen_en_modo_api(ruta):
    app = _app_api()
    respuesta = app.test_client().get(ruta)
    assert respuesta.status_code == 404
    assert respuesta.content_type != "application/json"
