from app import create_app
from tests.conftest import overrides_de_prueba


def test_health_responde_ok(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == "ok"


def test_health_responde_ok_con_base_inalcanzable():
    app = create_app(
        overrides_de_prueba(DATABASE_URL="postgresql://user:pass@localhost:1/db")
    )
    with app.test_client() as client:
        respuesta = client.get("/health")
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
