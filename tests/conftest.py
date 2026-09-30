import os

import pytest

from app import create_app


def pytest_configure(config):
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.exit(
            "TEST_DATABASE_URL no está definida. "
            "Defínela antes de ejecutar las pruebas (nunca uses DATABASE_URL)."
        )
    if "neon.tech" in test_database_url:
        pytest.exit("TEST_DATABASE_URL apunta a Neon. Las pruebas nunca deben ejecutarse contra Neon.")


def overrides_de_prueba(**extra):
    base = {
        "SECRET_KEY": "s" * 32,
        "DATABASE_URL": os.environ["TEST_DATABASE_URL"],
    }
    base.update(extra)
    return base


@pytest.fixture
def app():
    return create_app(overrides_de_prueba())


@pytest.fixture
def client(app):
    return app.test_client()
