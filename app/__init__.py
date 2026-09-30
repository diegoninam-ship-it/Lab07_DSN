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

    # Paso 5 y siguientes: modelos, y blueprints web o api según APP_MODE

    @app.context_processor
    def inyectar_servidor():
        return {"server_id": app.config["SERVER_ID"]}

    return app