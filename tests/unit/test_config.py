import pytest

from app.config import ConfiguracionInvalida, construir_configuracion

URL_VALIDA = "postgresql://user:pass@localhost/db"
SECRET_VALIDO = "s" * 32


def base(**extra):
    overrides = {"SECRET_KEY": SECRET_VALIDO, "DATABASE_URL": URL_VALIDA}
    overrides.update(extra)
    return overrides


def test_secret_key_faltante():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion({"DATABASE_URL": URL_VALIDA})


def test_secret_key_corto():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(SECRET_KEY="corto"))


def test_database_url_faltante():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion({"SECRET_KEY": SECRET_VALIDO})


def test_database_url_normalizada():
    config = construir_configuracion(base())
    assert config["SQLALCHEMY_DATABASE_URI"] == "postgresql+psycopg://user:pass@localhost/db"


def test_database_url_ya_normalizada_se_conserva():
    config = construir_configuracion(
        base(DATABASE_URL="postgresql+psycopg://user:pass@localhost/db")
    )
    assert config["SQLALCHEMY_DATABASE_URI"] == "postgresql+psycopg://user:pass@localhost/db"


def test_database_url_esquema_invalido():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(DATABASE_URL="mysql://user:pass@localhost/db"))


def test_use_direct_db_requiere_database_url_direct():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(USE_DIRECT_DB="1"))


def test_use_direct_db_usa_url_directa():
    config = construir_configuracion(
        base(USE_DIRECT_DB="1", DATABASE_URL_DIRECT="postgresql://a:b@host/db")
    )
    assert config["SQLALCHEMY_DATABASE_URI"] == "postgresql+psycopg://a:b@host/db"


@pytest.mark.parametrize("valor", ["2", "si", "true", ""])
def test_use_direct_db_valor_invalido(valor):
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(USE_DIRECT_DB=valor))


def test_server_id_por_defecto_es_hostname():
    config = construir_configuracion(base())
    assert config["SERVER_ID"]


def test_server_id_no_ascii():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(SERVER_ID="Servidor-ñ"))


def test_server_id_vacio():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(SERVER_ID=""))


def test_server_id_demasiado_largo():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(SERVER_ID="x" * 101))


def test_server_id_valido_limite():
    config = construir_configuracion(base(SERVER_ID="x" * 100))
    assert config["SERVER_ID"] == "x" * 100


def test_app_mode_invalido():
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(APP_MODE="invalido"))


@pytest.mark.parametrize("modo", ["web", "api"])
def test_app_mode_valido(modo):
    config = construir_configuracion(base(APP_MODE=modo))
    assert config["APP_MODE"] == modo


def test_app_mode_por_defecto_es_web():
    config = construir_configuracion(base())
    assert config["APP_MODE"] == "web"


@pytest.mark.parametrize("valor", ["999", "5000001", "abc", "", "1000.5"])
def test_carga_iteraciones_invalida(valor):
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(CARGA_ITERACIONES=valor))


@pytest.mark.parametrize("valor", ["1000", "5000000", "200000"])
def test_carga_iteraciones_valida(valor):
    config = construir_configuracion(base(CARGA_ITERACIONES=valor))
    assert config["CARGA_ITERACIONES"] == int(valor)


def test_carga_iteraciones_por_defecto():
    config = construir_configuracion(base())
    assert config["CARGA_ITERACIONES"] == 200_000


@pytest.mark.parametrize("nombre", ["LOAD_TEST", "SESSION_COOKIE_SECURE", "DETRAS_DE_PROXY"])
@pytest.mark.parametrize("valor", ["2", "si", "yes"])
def test_variables_booleanas_invalidas(nombre, valor):
    with pytest.raises(ConfiguracionInvalida):
        construir_configuracion(base(**{nombre: valor}))


def test_valores_fijos_de_configuracion():
    config = construir_configuracion(base())
    assert config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False
    assert config["SQLALCHEMY_ENGINE_OPTIONS"] == {
        "pool_pre_ping": True,
        "pool_size": 3,
        "max_overflow": 2,
        "pool_recycle": 300,
        "connect_args": {"connect_timeout": 10},
    }
    assert config["SESSION_COOKIE_HTTPONLY"] is True
    assert config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert config["WTF_I18N_ENABLED"] is False
    assert config["SESSION_COOKIE_SECURE"] is False
    assert config["LOAD_TEST"] is False
    assert config["DETRAS_DE_PROXY"] is False
