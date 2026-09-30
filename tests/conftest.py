import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa

from app import create_app

RAIZ = Path(__file__).resolve().parent.parent
TABLAS_DE_DATOS = ["productos", "usuarios"]


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


@pytest.fixture(scope="session")
def _motor_pruebas():
    engine = sa.create_engine(os.environ["TEST_DATABASE_URL"])
    yield engine
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _esquema_de_pruebas(_motor_pruebas):
    """Esquema limpio + migración real aplicada, una sola vez por sesión."""
    with _motor_pruebas.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))

    env = os.environ.copy()
    env["FLASK_APP"] = "wsgi"
    env["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
    env.pop("USE_DIRECT_DB", None)
    resultado = subprocess.run(
        [sys.executable, "-m", "flask", "db", "upgrade"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
    )
    if resultado.returncode != 0:
        pytest.exit(
            "No se pudo aplicar la migración a la base de pruebas:\n"
            + resultado.stdout
            + resultado.stderr
        )
    yield


@pytest.fixture(autouse=True)
def _truncar_tablas(_motor_pruebas):
    yield
    with _motor_pruebas.begin() as conn:
        conn.execute(sa.text(f"TRUNCATE {', '.join(TABLAS_DE_DATOS)} RESTART IDENTITY CASCADE"))


@pytest.fixture
def app():
    return create_app(overrides_de_prueba())


@pytest.fixture
def client(app):
    return app.test_client()
