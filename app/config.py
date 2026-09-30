import os
import socket


class ConfiguracionInvalida(RuntimeError):
    """La configuración obligatoria falta o no es válida."""


def _obtener(overrides, nombre, default=None):
    if nombre in overrides:
        return overrides[nombre]
    return os.environ.get(nombre, default)


def _requerido(overrides, nombre):
    valor = _obtener(overrides, nombre)
    if valor is None or valor == "":
        raise ConfiguracionInvalida(f"Falta la variable obligatoria {nombre}.")
    return valor


def _booleano(overrides, nombre, default="0"):
    valor = _obtener(overrides, nombre, default)
    if valor not in ("0", "1"):
        raise ConfiguracionInvalida(f"{nombre} debe ser '0' o '1', se recibió {valor!r}.")
    return valor == "1"


def _normalizar_url_db(nombre, valor):
    if valor.startswith("postgresql+psycopg://"):
        return valor
    if valor.startswith("postgresql://"):
        return "postgresql+psycopg://" + valor[len("postgresql://"):]
    raise ConfiguracionInvalida(
        f"{nombre} debe empezar con 'postgresql://' o 'postgresql+psycopg://'."
    )


def _validar_secret_key(valor):
    if len(valor) < 32:
        raise ConfiguracionInvalida("SECRET_KEY debe tener al menos 32 caracteres.")
    return valor


def _validar_server_id(overrides):
    valor = _obtener(overrides, "SERVER_ID")
    if valor is None:
        valor = socket.gethostname()
    if not (1 <= len(valor) <= 100) or not all(32 <= ord(c) <= 126 for c in valor):
        raise ConfiguracionInvalida(
            "SERVER_ID debe ser ASCII imprimible, de 1 a 100 caracteres."
        )
    return valor


def _validar_app_mode(overrides):
    valor = _obtener(overrides, "APP_MODE", "web")
    if valor not in ("web", "api"):
        raise ConfiguracionInvalida(f"APP_MODE inválido: {valor!r} (use 'web' o 'api').")
    return valor


def _validar_carga_iteraciones(overrides):
    valor = _obtener(overrides, "CARGA_ITERACIONES", "200000")
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ConfiguracionInvalida(
            f"CARGA_ITERACIONES debe ser un entero, se recibió {valor!r}."
        )
    if not (1_000 <= numero <= 5_000_000):
        raise ConfiguracionInvalida(
            "CARGA_ITERACIONES debe estar entre 1 000 y 5 000 000."
        )
    return numero


def construir_configuracion(config_overrides=None):
    """Construye y valida la configuración a partir del entorno.

    config_overrides usa los mismos nombres que las variables de entorno y
    tiene prioridad sobre ellas (necesario para crear varias apps de prueba
    en el mismo proceso con distinto SERVER_ID, SECRET_KEY o base de datos).
    """
    overrides = config_overrides or {}

    secret_key = _validar_secret_key(_requerido(overrides, "SECRET_KEY"))

    usar_db_directa = _booleano(overrides, "USE_DIRECT_DB", "0")
    if usar_db_directa:
        database_url = _normalizar_url_db(
            "DATABASE_URL_DIRECT", _requerido(overrides, "DATABASE_URL_DIRECT")
        )
    else:
        database_url = _normalizar_url_db(
            "DATABASE_URL", _requerido(overrides, "DATABASE_URL")
        )

    server_id = _validar_server_id(overrides)
    app_mode = _validar_app_mode(overrides)
    load_test = _booleano(overrides, "LOAD_TEST", "0")
    carga_iteraciones = _validar_carga_iteraciones(overrides)
    session_cookie_secure = _booleano(overrides, "SESSION_COOKIE_SECURE", "0")
    detras_de_proxy = _booleano(overrides, "DETRAS_DE_PROXY", "0")

    return {
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_size": 3,
            "max_overflow": 2,
            "pool_recycle": 300,
        },
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": session_cookie_secure,
        "WTF_I18N_ENABLED": False,
        "SERVER_ID": server_id,
        "APP_MODE": app_mode,
        "LOAD_TEST": load_test,
        "CARGA_ITERACIONES": carga_iteraciones,
        "DETRAS_DE_PROXY": detras_de_proxy,
    }
