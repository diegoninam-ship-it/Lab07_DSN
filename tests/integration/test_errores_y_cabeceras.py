from app import create_app
from app.extensions import db
from app.models import Usuario
from tests.conftest import overrides_de_prueba


def _app_web(**overrides):
    app = create_app(overrides_de_prueba(**overrides))
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def _crear_usuario(app):
    with app.app_context():
        usuario = Usuario(nombre="Usuario Demo", correo="demo@lab07.pe")
        usuario.set_password("Demo1234!")
        db.session.add(usuario)
        db.session.commit()


def test_pagina_404_en_modo_api_no_falla_con_cookie_de_sesion_web():
    app_web = _app_web(SERVER_ID="Backend 1 - 8081")
    _crear_usuario(app_web)
    respuesta_login = app_web.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    valor_cookie = respuesta_login.headers["Set-Cookie"].split(";")[0].split("=", 1)[1]

    app_api = create_app(overrides_de_prueba(APP_MODE="api"))
    cliente_api = app_api.test_client()
    cliente_api.set_cookie("session", valor_cookie)
    respuesta = cliente_api.get("/login")
    assert respuesta.status_code == 404
    assert "Atendido por" in respuesta.get_data(as_text=True)


def test_x_servidor_en_200(client):
    respuesta = client.get("/health")
    assert respuesta.headers["X-Servidor"]


def test_x_servidor_en_302():
    app = _app_web()
    respuesta = app.test_client().get("/")
    assert respuesta.status_code == 302
    assert "X-Servidor" in respuesta.headers


def test_x_servidor_en_400_csrf():
    app = create_app(overrides_de_prueba(SERVER_ID="Backend-X"))
    _crear_usuario(app)
    respuesta = app.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    assert respuesta.status_code == 400
    assert respuesta.headers["X-Servidor"] == "Backend-X"


def test_x_servidor_en_404(client):
    respuesta = client.get("/no-existe")
    assert respuesta.status_code == 404
    assert "X-Servidor" in respuesta.headers


def test_x_servidor_en_405():
    app = _app_web()
    respuesta = app.test_client().get("/logout")
    assert respuesta.status_code == 405
    assert "X-Servidor" in respuesta.headers


def test_x_servidor_en_500_y_json():
    app = create_app(overrides_de_prueba(SERVER_ID="Backend-X", APP_MODE="api"))

    @app.route("/_prueba_500")
    def _lanzar_excepcion():
        raise RuntimeError("boom")

    respuesta = app.test_client().get("/_prueba_500")
    assert respuesta.status_code == 500
    assert respuesta.headers["X-Servidor"] == "Backend-X"


def test_pagina_404_propia_sin_traceback():
    app = _app_web()
    respuesta = app.test_client().get("/no-existe")
    html = respuesta.get_data(as_text=True)
    assert "Página no disponible" in html
    assert "Atendido por" in html
    assert "Traceback" not in html


def test_pagina_csrf_propia_explica_formulario_expirado():
    app = create_app(overrides_de_prueba())
    _crear_usuario(app)
    respuesta = app.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    html = respuesta.get_data(as_text=True)
    assert "formulario expiró" in html.lower() or "recarga" in html.lower()
    assert "Atendido por" in html


def test_pagina_500_propia_sin_traceback():
    app = _app_web()

    @app.route("/_prueba_500")
    def _lanzar_excepcion():
        raise RuntimeError("boom")

    respuesta = app.test_client().get("/_prueba_500")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 500
    assert "Ocurrió un error" in html
    assert "Atendido por" in html
    assert "Traceback" not in html
    assert "RuntimeError" not in html


def test_500_en_modo_api_es_json_sin_traceback():
    app = create_app(overrides_de_prueba(APP_MODE="api"))

    @app.route("/api/_prueba_500")
    def _lanzar_excepcion():
        raise RuntimeError("boom")

    respuesta = app.test_client().get("/api/_prueba_500")
    assert respuesta.status_code == 500
    datos = respuesta.get_json()
    assert "RuntimeError" not in str(datos)


def test_css_servido_desde_static():
    app = _app_web()
    respuesta = app.test_client().get("/static/css/app.css")
    assert respuesta.status_code == 200
    assert "text/css" in respuesta.content_type


def test_pie_de_pagina_presente_en_pagina_html():
    app = _app_web()
    respuesta = app.test_client().get("/login")
    html = respuesta.get_data(as_text=True)
    assert "Atendido por" in html
