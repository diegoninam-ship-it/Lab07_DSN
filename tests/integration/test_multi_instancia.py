import re

from app import create_app
from app.extensions import db
from app.models import Producto, Usuario
from tests.conftest import overrides_de_prueba

SECRET_COMPARTIDO = "s" * 32


def _app(secret_key=SECRET_COMPARTIDO, **overrides):
    return create_app(overrides_de_prueba(SECRET_KEY=secret_key, **overrides))


def _crear_usuario(app, correo="demo@lab07.pe", password="Demo1234!"):
    with app.app_context():
        usuario = Usuario(nombre="Usuario Demo", correo=correo)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()


def _valor_cookie_sesion(respuesta):
    set_cookie = respuesta.headers.get("Set-Cookie")
    assert set_cookie is not None
    return set_cookie.split(";")[0].split("=", 1)[1]


def _extraer_csrf_token(html):
    campo = re.search(r'<input[^>]*name="csrf_token"[^>]*>', html).group(0)
    return re.search(r'value="([^"]+)"', campo).group(1)


def test_login_en_a_cookie_usada_en_b():
    app_a = _app(SERVER_ID="Backend 1 - 8081")
    app_a.config["WTF_CSRF_ENABLED"] = False
    app_b = _app(SERVER_ID="Backend 2 - 8082")
    app_b.config["WTF_CSRF_ENABLED"] = False
    _crear_usuario(app_a)

    respuesta_login = app_a.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    valor_cookie = _valor_cookie_sesion(respuesta_login)

    cliente_b = app_b.test_client()
    cliente_b.set_cookie("session", valor_cookie)
    respuesta_b = cliente_b.get("/")
    assert respuesta_b.status_code == 200


def test_formulario_generado_por_a_enviado_a_b_csrf_aceptado():
    app_a = _app(SERVER_ID="Backend 1 - 8081")
    app_b = _app(SERVER_ID="Backend 2 - 8082")
    _crear_usuario(app_a)

    pagina_login = app_a.test_client().get("/login")
    token = _extraer_csrf_token(pagina_login.get_data(as_text=True))
    valor_cookie = _valor_cookie_sesion(pagina_login)

    cliente_b = app_b.test_client()
    cliente_b.set_cookie("session", valor_cookie)
    respuesta = cliente_b.post(
        "/login",
        data={"correo": "demo@lab07.pe", "password": "Demo1234!", "csrf_token": token},
    )
    assert respuesta.status_code == 302


def test_cookie_de_instancia_web_usada_en_instancia_api():
    app_web = _app(SERVER_ID="Backend 1 - 8081", APP_MODE="web")
    app_web.config["WTF_CSRF_ENABLED"] = False
    app_api = _app(SERVER_ID="API-1", APP_MODE="api")
    _crear_usuario(app_web)

    respuesta_login = app_web.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    valor_cookie = _valor_cookie_sesion(respuesta_login)

    cliente_api = app_api.test_client()
    cliente_api.set_cookie("session", valor_cookie)
    respuesta_api = cliente_api.get("/api/productos")
    assert respuesta_api.status_code == 200


def test_crear_en_a_editar_en_b():
    app_a = _app(SERVER_ID="Backend 1 - 8081")
    app_a.config["WTF_CSRF_ENABLED"] = False
    app_b = _app(SERVER_ID="Backend 2 - 8082")
    app_b.config["WTF_CSRF_ENABLED"] = False
    _crear_usuario(app_a)

    cliente_a = app_a.test_client()
    cliente_a.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
    cliente_a.post("/productos/nuevo", data={"nombre": "Cable HDMI", "precio": "7.50", "stock": "4"})

    with app_a.app_context():
        producto_id = db.session.execute(db.select(Producto)).scalar_one().id

    cliente_b = app_b.test_client()
    cliente_b.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
    respuesta = cliente_b.post(
        f"/productos/{producto_id}/editar",
        data={"nombre": "Cable HDMI 2m", "precio": "8.00", "stock": "6"},
    )
    assert respuesta.status_code == 302

    with app_a.app_context():
        producto = db.session.get(Producto, producto_id)
        assert producto.servidor_origen == "Backend 1 - 8081"
        assert producto.servidor_actualizacion == "Backend 2 - 8082"


def test_control_negativo_secret_key_distinto_cookie_rechazada():
    app_a = _app(secret_key=SECRET_COMPARTIDO, SERVER_ID="Backend 1 - 8081")
    app_a.config["WTF_CSRF_ENABLED"] = False
    app_otro = _app(secret_key="o" * 32, SERVER_ID="Backend 2 - 8082")
    app_otro.config["WTF_CSRF_ENABLED"] = False
    _crear_usuario(app_a)

    respuesta_login = app_a.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    valor_cookie = _valor_cookie_sesion(respuesta_login)

    cliente_otro = app_otro.test_client()
    cliente_otro.set_cookie("session", valor_cookie)
    respuesta = cliente_otro.get("/")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/login?next=/"
