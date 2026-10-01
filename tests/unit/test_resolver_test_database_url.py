import pytest

from tests.conftest import ConfiguracionDePruebasInvalida, resolver_test_database_url


def test_gana_la_variable_de_entorno(tmp_path):
    ruta_env = tmp_path / ".env"
    ruta_env.write_text("TEST_DATABASE_URL=postgresql://del-env-file/db\n")

    valor = resolver_test_database_url(
        {"TEST_DATABASE_URL": "postgresql://de-la-variable/db"}, ruta_env
    )

    assert valor == "postgresql://de-la-variable/db"


def test_respaldo_desde_el_env(tmp_path):
    ruta_env = tmp_path / ".env"
    ruta_env.write_text("TEST_DATABASE_URL=postgresql://lab07:lab07@localhost:5433/lab07_test\n")

    valor = resolver_test_database_url({}, ruta_env)

    assert valor == "postgresql://lab07:lab07@localhost:5433/lab07_test"


def test_respaldo_no_contamina_el_entorno(tmp_path):
    ruta_env = tmp_path / ".env"
    ruta_env.write_text("TEST_DATABASE_URL=postgresql://lab07:lab07@localhost:5433/lab07_test\n")
    entorno = {}

    resolver_test_database_url(entorno, ruta_env)

    assert entorno == {}


def test_rechazo_de_neon_desde_la_variable_de_entorno(tmp_path):
    with pytest.raises(ConfiguracionDePruebasInvalida, match="Neon"):
        resolver_test_database_url(
            {"TEST_DATABASE_URL": "postgresql://user@host.neon.tech/db"}, tmp_path / ".env"
        )


def test_rechazo_de_neon_desde_el_env(tmp_path):
    ruta_env = tmp_path / ".env"
    ruta_env.write_text("TEST_DATABASE_URL=postgresql://user@host.neon.tech/db\n")

    with pytest.raises(ConfiguracionDePruebasInvalida, match="Neon"):
        resolver_test_database_url({}, ruta_env)


def test_ausencia_total(tmp_path):
    with pytest.raises(ConfiguracionDePruebasInvalida, match="no está definida"):
        resolver_test_database_url({}, tmp_path / ".env")
