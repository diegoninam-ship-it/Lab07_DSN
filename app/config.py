import os


class Config:
    # Falla al arrancar si faltan: mejor que un error a mitad de una petición
    SECRET_KEY = os.environ["SECRET_KEY"]

    # Migraciones con la URL directa (sin pooler); la app, siempre con pooler
    if os.environ.get("USE_DIRECT_DB") == "1":
        SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL_DIRECT"]
    else:
        SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Neon cierra conexiones inactivas
        "pool_size": 3,          # varios workers × varias instancias: pool pequeño
        "max_overflow": 2,
        "pool_recycle": 300,
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Sin SESSION_COOKIE_SECURE: el ALB solo expone HTTP (limitación documentada)

    SERVER_ID = os.environ.get("SERVER_ID", "desconocido")
    APP_MODE = os.environ.get("APP_MODE", "web")
    LOAD_TEST = os.environ.get("LOAD_TEST", "0") == "1"