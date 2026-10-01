from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

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

    if app.config["APP_MODE"] == "web":
        from app.blueprints.auth import bp as auth_bp
        from app.blueprints.productos import bp as productos_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(productos_bp)
    elif app.config["APP_MODE"] == "api":
        from app.blueprints.api import bp as api_bp

        app.register_blueprint(api_bp)

    @app.context_processor
    def inyectar_servidor():
        return {"server_id": app.config["SERVER_ID"]}

    @app.after_request
    def agregar_cabecera_servidor(response):
        response.headers["X-Servidor"] = app.config["SERVER_ID"]
        return response

    def _bajo_api():
        return request.path.startswith("/api/")

    @app.errorhandler(CSRFError)
    def manejar_csrf(error):
        if _bajo_api():
            return jsonify(error="Solicitud inválida"), 400
        return render_template("errores/400.html"), 400

    @app.errorhandler(404)
    def manejar_404(error):
        if _bajo_api():
            return jsonify(error="No encontrado"), 404
        return render_template("errores/404.html"), 404

    @app.errorhandler(405)
    def manejar_405(error):
        if _bajo_api():
            return jsonify(error="Método no permitido"), 405
        return render_template("errores/404.html"), 405

    @app.errorhandler(500)
    def manejar_500(error):
        if _bajo_api():
            return jsonify(error="Error interno"), 500
        return render_template("errores/500.html"), 500

    from app.cli import register_cli

    register_cli(app)

    return app
