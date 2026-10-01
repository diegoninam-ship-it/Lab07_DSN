from app import create_app
from tests.conftest import overrides_de_prueba


def test_detras_de_proxy_aplica_proxy_fix():
    app = create_app(overrides_de_prueba(DETRAS_DE_PROXY="1"))
    respuesta = app.test_client().get(
        "/whoami", headers={"X-Forwarded-For": "203.0.113.5", "X-Forwarded-Proto": "https"}
    )
    assert respuesta.status_code == 200
