from app import create_app
from app.extensions import db
from app.models import Usuario
from tests.conftest import overrides_de_prueba

DATABASE_URL_INALCANZABLE = "postgresql://user:pass@localhost:1/db?connect_timeout=2"


def _valor_cookie_sesion_valida():
    """Inicia sesión en una app con base alcanzable y devuelve el valor de la
    cookie, para reutilizarlo contra una instancia cuya base esté caída
    (mismo SECRET_KEY: overrides_de_prueba usa uno fijo por defecto)."""
    app = create_app(overrides_de_prueba())
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        usuario = Usuario(nombre="Usuario Demo", correo="demo@lab07.pe")
        usuario.set_password("Demo1234!")
        db.session.add(usuario)
        db.session.commit()

    respuesta = app.test_client().post(
        "/login", data={"correo": "demo@lab07.pe", "password": "Demo1234!"}
    )
    set_cookie = respuesta.headers.get("Set-Cookie")
    assert set_cookie is not None
    return set_cookie.split(";")[0].split("=", 1)[1]


def test_health_responde_ok(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "ok"


def test_health_responde_ok_con_base_inalcanzable():
    app = create_app(overrides_de_prueba(DATABASE_URL=DATABASE_URL_INALCANZABLE))
    with app.test_client() as client:
        respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "ok"


def test_health_responde_ok_con_base_inalcanzable_y_sesion_valida():
    valor_cookie = _valor_cookie_sesion_valida()
    app = create_app(overrides_de_prueba(DATABASE_URL=DATABASE_URL_INALCANZABLE))
    client = app.test_client()
    client.set_cookie("session", valor_cookie)
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "ok"


def test_whoami_responde_ok_con_base_inalcanzable_y_sesion_valida():
    valor_cookie = _valor_cookie_sesion_valida()
    app = create_app(
        overrides_de_prueba(DATABASE_URL=DATABASE_URL_INALCANZABLE, SERVER_ID="Servidor-Prueba")
    )
    client = app.test_client()
    client.set_cookie("session", valor_cookie)
    respuesta = client.get("/whoami")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "Servidor-Prueba"


def test_carga_responde_ok_con_base_inalcanzable_y_sesion_valida():
    valor_cookie = _valor_cookie_sesion_valida()
    app = create_app(
        overrides_de_prueba(
            DATABASE_URL=DATABASE_URL_INALCANZABLE,
            LOAD_TEST="1",
            CARGA_ITERACIONES="1000",
            SERVER_ID="Servidor-Carga",
        )
    )
    client = app.test_client()
    client.set_cookie("session", valor_cookie)
    respuesta = client.get("/carga")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "carga completada en Servidor-Carga"


def test_api_test_responde_ok_con_base_inalcanzable_y_sesion_valida():
    valor_cookie = _valor_cookie_sesion_valida()
    app = create_app(
        overrides_de_prueba(
            DATABASE_URL=DATABASE_URL_INALCANZABLE, APP_MODE="api", SERVER_ID="API-1"
        )
    )
    client = app.test_client()
    client.set_cookie("session", valor_cookie)
    respuesta = client.get("/api/test")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "API SERVER · API-1"


def test_api_health_responde_ok_con_base_inalcanzable_y_sesion_valida():
    valor_cookie = _valor_cookie_sesion_valida()
    app = create_app(
        overrides_de_prueba(DATABASE_URL=DATABASE_URL_INALCANZABLE, APP_MODE="api")
    )
    client = app.test_client()
    client.set_cookie("session", valor_cookie)
    respuesta = client.get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "ok"


def test_whoami_devuelve_server_id(client):
    app = create_app(overrides_de_prueba(SERVER_ID="Servidor-Prueba"))
    with app.test_client() as c:
        respuesta = c.get("/whoami")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "Servidor-Prueba"
    assert respuesta.content_type == "text/plain; charset=utf-8"


def test_carga_responde_404_si_load_test_desactivado(client):
    respuesta = client.get("/carga")
    assert respuesta.status_code == 404


def test_carga_responde_200_si_load_test_activado():
    app = create_app(
        overrides_de_prueba(LOAD_TEST="1", CARGA_ITERACIONES="1000", SERVER_ID="Servidor-Carga")
    )
    with app.test_client() as c:
        respuesta = c.get("/carga")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "carga completada en Servidor-Carga"
