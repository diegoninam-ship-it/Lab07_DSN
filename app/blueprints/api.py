from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request

from app.blueprints.auth import usuario_de_sesion
from app.extensions import db
from app.models import Producto

bp = Blueprint("api", __name__, url_prefix="/api")


def api_login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        usuario = usuario_de_sesion()
        if usuario is None:
            return jsonify(error="No autenticado"), 401
        g.usuario = usuario
        return vista(*args, **kwargs)

    return envoltura


@bp.get("/test")
def test():
    return f"API SERVER · {current_app.config['SERVER_ID']}", 200, {"Content-Type": "text/plain; charset=utf-8"}


@bp.get("/health")
def health():
    return "ok", 200


@bp.get("/productos")
@api_login_required
def lista():
    # type=int devuelve el valor por defecto si el texto no es un número; luego se acota el rango
    limite = min(max(request.args.get("limite", 50, type=int), 1), 200)
    pagina = min(max(request.args.get("pagina", 1, type=int), 1), 1_000_000)
    consulta = (
        db.select(Producto).order_by(Producto.id.desc()).limit(limite).offset((pagina - 1) * limite)
    )
    productos = db.session.execute(consulta).scalars().all()
    total = db.session.scalar(db.select(db.func.count()).select_from(Producto))
    return jsonify(
        servidor=current_app.config["SERVER_ID"],
        total=total,
        pagina=pagina,
        limite=limite,
        productos=[p.to_dict() for p in productos],
    )


@bp.get("/productos/<int(max=2147483647):producto_id>")
@api_login_required
def detalle(producto_id):
    producto = db.session.get(Producto, producto_id)
    if producto is None:
        return jsonify(error="Producto no encontrado"), 404
    return jsonify(producto.to_dict())
