from dotenv import load_dotenv

load_dotenv()  # antes de importar Config, que lee os.environ al cargarse

from flask import Flask  # noqa: E402

from app.config import Config  # noqa: E402
from app.extensions import csrf, db, migrate  # noqa: E402


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app import models  # noqa: F401 — registra las tablas para Flask-Migrate
    from app.publico import bp as publico_bp
    app.register_blueprint(publico_bp)  # /health, /whoami, /carga en ambos modos

    if app.config["APP_MODE"] == "web":
        from app.auth import bp as auth_bp
        from app.productos import bp as productos_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(productos_bp)
    # APP_MODE=api: el blueprint de la API se agrega para el Ejercicio 4

    @app.context_processor
    def inyectar_servidor():
        return {"server_id": app.config["SERVER_ID"]}

    from app.cli import register_cli
    register_cli(app)
    
    return app