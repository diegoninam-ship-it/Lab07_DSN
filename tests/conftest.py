import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from dotenv import dotenv_values

from app import create_app

RAIZ = Path(__file__).resolve().parent.parent
TABLAS_DE_DATOS = ["productos", "usuarios"]

_test_database_url = None


class ConfiguracionDePruebasInvalida(Exception):
    """TEST_DATABASE_URL falta o apunta a Neon."""


def resolver_test_database_url(entorno, ruta_env):
    """Resuelve TEST_DATABASE_URL en orden: (1) variable de entorno;
    (2) solo esa clave leída de ``ruta_env`` con ``dotenv_values`` —sin
    ``load_dotenv`` y sin tocar ``os.environ``, para no contaminar las
    pruebas de configuración—; (3) si no aparece en ninguna de las dos,
    ``ConfiguracionDePruebasInvalida``. El rechazo de ``neon.tech`` se
    aplica al valor resuelto, venga de donde venga.
    """
    valor = entorno.get("TEST_DATABASE_URL") or dotenv_values(ruta_env).get("TEST_DATABASE_URL")
    if not valor:
        raise ConfiguracionDePruebasInvalida(
            "TEST_DATABASE_URL no está definida (ni en el entorno ni en .env). "
            "Defínela antes de ejecutar las pruebas (nunca uses DATABASE_URL)."
        )
    if "neon.tech" in valor:
        raise ConfiguracionDePruebasInvalida(
            "TEST_DATABASE_URL apunta a Neon. Las pruebas nunca deben ejecutarse contra Neon."
        )
    return valor


def pytest_configure(config):
    global _test_database_url
    try:
        _test_database_url = resolver_test_database_url(os.environ, RAIZ / ".env")
    except ConfiguracionDePruebasInvalida as error:
        pytest.exit(str(error))


def overrides_de_prueba(**extra):
    base = {
        "SECRET_KEY": "s" * 32,
        "DATABASE_URL": _test_database_url,
    }
    base.update(extra)
    return base


@pytest.fixture(scope="session")
def _motor_pruebas():
    engine = sa.create_engine(_test_database_url)
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
    env["DATABASE_URL"] = _test_database_url
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
