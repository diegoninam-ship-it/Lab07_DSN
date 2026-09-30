from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app.extensions import db
from app.forms import LoginForm
from app.models import Usuario

bp = Blueprint("auth", __name__)


def _destino_seguro(destino):
    """Solo rutas internas: evita que ?next= redirija a un sitio externo."""
    if destino and destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return destino
    return None


def usuario_de_sesion():
    """Usuario de la sesión o None. Limpia la cookie si apunta a un usuario que ya no existe."""
    usuario_id = session.get("usuario_id")
    usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None and usuario_id is not None:
        session.clear()
    return usuario


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        usuario = usuario_de_sesion()
        if usuario is None:
            return redirect(url_for("auth.login", next=request.path))
        g.usuario = usuario
        return vista(*args, **kwargs)

    return envoltura


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return redirect(url_for("productos.lista"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = db.session.execute(
            db.select(Usuario).filter_by(correo=form.correo.data.strip().lower())
        ).scalar_one_or_none()

        if usuario and usuario.check_password(form.password.data):
            session.clear()
            session["usuario_id"] = usuario.id
            return redirect(_destino_seguro(request.args.get("next")) or url_for("productos.lista"))

        flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html", form=form)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))