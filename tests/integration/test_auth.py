import re

from app import create_app
from app.extensions import db
from app.models import Usuario
from tests.conftest import overrides_de_prueba


def _crear_usuario(app, correo="demo@lab07.pe", password="Demo1234!", nombre="Usuario Demo"):
    with app.app_context():
        usuario = Usuario(nombre=nombre, correo=correo)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        return usuario.id


def _app_sin_csrf(**overrides):
    app = create_app(overrides_de_prueba(**overrides))
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def _extraer_csrf_token(html):
    campo = re.search(r'<input[^>]*name="csrf_token"[^>]*>', html).group(0)
    return re.search(r'value="([^"]+)"', campo).group(1)


def test_login_correcto_redirige_y_guarda_solo_usuario_id():
    app = _app_sin_csrf()
    usuario_id = _crear_usuario(app)
    with app.test_client() as client:
        respuesta = client.post(
            "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
        )
        assert respuesta.status_code == 302
        with client.session_transaction() as sesion:
            assert dict(sesion) == {"usuario_id": usuario_id}


def test_login_incorrecto_mensaje_unico():
    app = _app_sin_csrf()
    _crear_usuario(app)

    with app.test_client() as client:
        respuesta_clave_mala = client.post(
            "/login", data={"correo": "demo@lab07.pe", "password": "incorrecta"}, follow_redirects=True
        )
    with app.test_client() as client:
        respuesta_correo_inexistente = client.post(
            "/login", data={"correo": "nadie@lab07.pe", "password": "cualquiera"}, follow_redirects=True
        )

    assert "Correo o contraseña incorrectos." in respuesta_clave_mala.get_data(as_text=True)
    assert "Correo o contraseña incorrectos." in respuesta_correo_inexistente.get_data(as_text=True)


def test_correo_con_mayusculas_y_espacios():
    app = _app_sin_csrf()
    _crear_usuario(app, correo="demo@lab07.pe")
    with app.test_client() as client:
        respuesta = client.post(
            "/login", data={"correo": "  DEMO@LAB07.PE  ", "password": "Demo1234!"}
        )
    assert respuesta.status_code == 302


def test_next_seguro_se_respeta():
    app = _app_sin_csrf()
    _crear_usuario(app)
    with app.test_client() as client:
        respuesta = client.post(
            "/login?next=/productos/nuevo",
            data={"correo": "demo@lab07.pe", "password": "Demo1234!"},
        )
    assert respuesta.headers["Location"] == "/productos/nuevo"


def test_next_inseguro_se_ignora():
    app = _app_sin_csrf()
    _crear_usuario(app)
    for destino_malicioso in ["//externo.com", "/\\externo.com", "https://externo.com"]:
        with app.test_client() as client:
            respuesta = client.post(
                f"/login?next={destino_malicioso}",
                data={"correo": "demo@lab07.pe", "password": "Demo1234!"},
            )
        assert respuesta.headers["Location"] == "/"


def test_logout_get_no_permitido():
    app = _app_sin_csrf()
    with app.test_client() as client:
        respuesta = client.get("/logout")
    assert respuesta.status_code == 405


def test_logout_post_limpia_sesion():
    app = _app_sin_csrf()
    _crear_usuario(app)
    with app.test_client() as client:
        client.post("/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"})
        respuesta = client.post("/logout")
        with client.session_transaction() as sesion:
            assert dict(sesion) == {}
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"] == "/login"


def test_csrf_obligatorio_en_login():
    app = create_app(overrides_de_prueba())
    _crear_usuario(app)
    with app.test_client() as client:
        respuesta = client.post(
            "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
        )
    assert respuesta.status_code == 400


def test_login_con_csrf_valido_funciona():
    app = create_app(overrides_de_prueba())
    _crear_usuario(app)
    with app.test_client() as client:
        pagina = client.get("/login")
        token = _extraer_csrf_token(pagina.get_data(as_text=True))
        respuesta = client.post(
            "/login",
            data={"correo": "demo@lab07.pe", "password": "Demo1234!", "csrf_token": token},
        )
    assert respuesta.status_code == 302


def test_usuario_de_sesion_limpia_cookie_de_usuario_borrado():
    from flask import session

    from app.blueprints.auth import usuario_de_sesion

    app = _app_sin_csrf()
    usuario_id = _crear_usuario(app)
    with app.test_request_context():
        session["usuario_id"] = usuario_id
        db.session.delete(db.session.get(Usuario, usuario_id))
        db.session.commit()

        assert usuario_de_sesion() is None
        assert dict(session) == {}
