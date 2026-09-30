import hashlib

from flask import Blueprint, abort, current_app

bp = Blueprint("publico", __name__)


@bp.get("/health")
def health():
    # No toca la BD: una caída de Neon no debe tumbar todos los targets del ALB
    return "ok", 200


@bp.get("/whoami")
def whoami():
    return current_app.config["SERVER_ID"], 200, {"Content-Type": "text/plain; charset=utf-8"}


@bp.get("/carga")
def carga():
    if not current_app.config["LOAD_TEST"]:
        abort(404)
    dato = b"lab07"
    for _ in range(200_000):
        dato = hashlib.sha256(dato).digest()
    return f"carga completada en {current_app.config['SERVER_ID']}", 200