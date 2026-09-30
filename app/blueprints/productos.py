from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.blueprints.auth import login_required
from app.extensions import db
from app.forms import ProductoForm
from app.models import Producto

bp = Blueprint("productos", __name__)


@bp.get("/")
@login_required
def lista():
    productos = db.session.execute(db.select(Producto).order_by(Producto.id.desc())).scalars().all()
    return render_template("productos/lista.html", productos=productos)


@bp.route("/productos/nuevo", methods=["GET", "POST"])
@login_required
def crear():
    form = ProductoForm()
    if form.validate_on_submit():
        producto = Producto(
            nombre=form.nombre.data.strip(),
            precio=form.precio.data,
            stock=form.stock.data,
            servidor_origen=current_app.config["SERVER_ID"],
        )
        db.session.add(producto)
        db.session.commit()
        flash(f"Producto creado (atendido por {producto.servidor_origen}).", "ok")
        return redirect(url_for("productos.lista"))
    return render_template("productos/form.html", form=form, titulo="Nuevo producto")


@bp.route("/productos/<int(max=2147483647):producto_id>/editar", methods=["GET", "POST"])
@login_required
def editar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    form = ProductoForm(obj=producto)
    if form.validate_on_submit():
        producto.nombre = form.nombre.data.strip()
        producto.precio = form.precio.data
        producto.stock = form.stock.data
        producto.servidor_actualizacion = current_app.config["SERVER_ID"]
        db.session.commit()
        flash("Producto actualizado.", "ok")
        return redirect(url_for("productos.lista"))
    return render_template("productos/form.html", form=form, titulo="Editar producto")


@bp.post("/productos/<int(max=2147483647):producto_id>/eliminar")
@login_required
def eliminar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado.", "ok")
    return redirect(url_for("productos.lista"))
