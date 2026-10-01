from app import create_app
from app.extensions import db
from app.models import Producto, Usuario
from tests.conftest import overrides_de_prueba


def _app_sin_csrf(**overrides):
    app = create_app(overrides_de_prueba(**overrides))
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def _crear_usuario(app, correo="demo@lab07.pe", password="Demo1234!"):
    with app.app_context():
        usuario = Usuario(nombre="Usuario Demo", correo=correo)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()


def _cliente_autenticado(app):
    client = app.test_client()
    client.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
    return client


def test_formulario_nuevo_producto_se_renderiza():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    respuesta = client.get("/productos/nuevo")
    assert respuesta.status_code == 200


def test_formulario_nuevo_producto_invalido_reeemite_el_formulario():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    respuesta = client.post("/productos/nuevo", data={"nombre": "", "precio": "1", "stock": "1"})
    assert respuesta.status_code == 200


def test_editar_producto_get_precarga_valores():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    client.post("/productos/nuevo", data={"nombre": "Silla", "precio": "50.00", "stock": "2"})
    with app.app_context():
        producto_id = db.session.execute(db.select(Producto)).scalar_one().id

    respuesta = client.get(f"/productos/{producto_id}/editar")
    assert respuesta.status_code == 200
    assert "Silla" in respuesta.get_data(as_text=True)


def test_lista_requiere_sesion():
    app = _app_sin_csrf()
    with app.test_client() as client:
        respuesta = client.get("/")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/login?next=/"


def test_crear_producto_registra_servidor_origen():
    app = _app_sin_csrf(SERVER_ID="Backend 1 - 8081")
    _crear_usuario(app)
    with app.test_client() as client:
        client.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
        respuesta = client.post(
            "/productos/nuevo", data={"nombre": "Teclado", "precio": "12.00", "stock": "5"}
        )
        assert respuesta.status_code == 302

    with app.app_context():
        producto = db.session.execute(db.select(Producto)).scalar_one()
        assert producto.servidor_origen == "Backend 1 - 8081"
        assert producto.servidor_actualizacion is None


def test_editar_producto_registra_servidor_actualizacion_sin_tocar_origen():
    app_a = _app_sin_csrf(SERVER_ID="Backend 1 - 8081")
    _crear_usuario(app_a)
    with app_a.test_client() as client_a:
        client_a.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
        client_a.post("/productos/nuevo", data={"nombre": "Mouse", "precio": "9.50", "stock": "2"})

    with app_a.app_context():
        producto_id = db.session.execute(db.select(Producto)).scalar_one().id

    app_b = _app_sin_csrf(SERVER_ID="Backend 2 - 8082")
    with app_b.test_client() as client_b:
        client_b.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
        respuesta = client_b.post(
            f"/productos/{producto_id}/editar",
            data={"nombre": "Mouse inalámbrico", "precio": "15.00", "stock": "3"},
        )
        assert respuesta.status_code == 302

    with app_a.app_context():
        producto = db.session.get(Producto, producto_id)
        assert producto.nombre == "Mouse inalámbrico"
        assert producto.servidor_origen == "Backend 1 - 8081"
        assert producto.servidor_actualizacion == "Backend 2 - 8082"


def test_editar_id_inexistente_404():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    respuesta = client.get("/productos/999999/editar")
    assert respuesta.status_code == 404


def test_editar_id_mayor_a_32_bits_404_sin_tocar_la_base():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    respuesta = client.get("/productos/99999999999/editar")
    assert respuesta.status_code == 404


def test_eliminar_por_get_no_permitido():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    respuesta = client.get("/productos/1/eliminar")
    assert respuesta.status_code == 405


def test_eliminar_producto():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    client.post("/productos/nuevo", data={"nombre": "Monitor", "precio": "100.00", "stock": "1"})
    with app.app_context():
        producto_id = db.session.execute(db.select(Producto)).scalar_one().id

    respuesta = client.post(f"/productos/{producto_id}/eliminar")
    assert respuesta.status_code == 302

    with app.app_context():
        assert db.session.get(Producto, producto_id) is None


def test_lista_escapa_html_y_confirm_no_incluye_datos_del_producto():
    app = _app_sin_csrf()
    _crear_usuario(app)
    client = _cliente_autenticado(app)
    client.post(
        "/productos/nuevo",
        data={"nombre": "<script>alert(1)</script>", "precio": "1.00", "stock": "1"},
    )

    respuesta = client.get("/")
    html = respuesta.get_data(as_text=True)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "confirm('¿Eliminar este producto?')" in html
