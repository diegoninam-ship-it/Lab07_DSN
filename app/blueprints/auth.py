from functools import wraps

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for

from app.extensions import db
from app.forms import LoginForm
from app.models import Usuario

bp = Blueprint("auth", __name__)


def _destino_seguro(destino):
    if destino and destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return destino
    return None


def usuario_de_sesion():
    """Usuario de la sesión o None. Limpia la cookie si apunta a un usuario que ya no existe."""
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return None
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None:
        session.clear()
    return usuario


def usuario_actual():
    """Usuario de la sesión, cacheado en g dentro de esta petición.

    Deliberadamente perezoso: nada lo invoca por defecto en cada petición (a
    diferencia de un before_request global), así que una ruta pública que
    nunca lo llama —/health, /whoami, /carga— jamás consulta la base, tenga
    o no cookie de sesión. Solo lo evalúan login_required y las plantillas
    que muestran el usuario autenticado.

    En modo api no hay login/logout propios: devuelve None sin tocar la
    sesión ni la base, para que una página de error (404/500) fuera de
    /api/ —que también extiende base.html— no intente enlazar a
    auth.logout, endpoint que no existe en ese modo.
    """
    if not hasattr(g, "_usuario_actual"):
        if current_app.config["APP_MODE"] == "web":
            g._usuario_actual = usuario_de_sesion()
        else:
            g._usuario_actual = None
    return g._usuario_actual


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if usuario_actual() is None:
            return redirect(url_for("auth.login", next=request.path))
        return vista(*args, **kwargs)

    return envoltura


@bp.route("/login", methods=["GET", "POST"])
def login():
    if usuario_actual() is not None:
        return redirect("/")

    form = LoginForm()
    if form.validate_on_submit():
        usuario = db.session.execute(
            db.select(Usuario).filter_by(correo=form.correo.data.strip().lower())
        ).scalar_one_or_none()

        if usuario and usuario.check_password(form.password.data):
            session.clear()
            session["usuario_id"] = usuario.id
            return redirect(_destino_seguro(request.args.get("next")) or "/")

        flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html", form=form)


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
