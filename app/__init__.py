from flask import Flask

from app.config import construir_configuracion
from app.extensions import csrf, db, migrate


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.update(construir_configuracion(config_overrides))

    if app.config["DETRAS_DE_PROXY"]:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app import models  # noqa: F401 — registra las tablas para Flask-Migrate

    from app.blueprints.publico import bp as publico_bp

    app.register_blueprint(publico_bp)

    from app.cli import register_cli

    register_cli(app)

    return app
