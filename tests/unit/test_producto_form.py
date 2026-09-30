import pytest
from werkzeug.datastructures import MultiDict

from app import create_app
from app.forms import ProductoForm
from tests.conftest import overrides_de_prueba


@pytest.fixture
def contexto_app():
    app = create_app(overrides_de_prueba())
    with app.test_request_context():
        yield


def _form(**datos):
    base = {"nombre": "Producto", "precio": "10.00", "stock": "1"}
    base.update(datos)
    return ProductoForm(formdata=MultiDict(base), meta={"csrf": False})


@pytest.mark.parametrize(
    "precio",
    ["-1", "10.123", "NaN", "Infinity", "-Infinity", "10,50", "abc", "", "100000000.00"],
)
def test_precio_invalido_produce_un_solo_error(contexto_app, precio):
    form = _form(precio=precio)
    form.validate()
    assert len(form.precio.errors) == 1
    assert form.nombre.errors == []
    assert form.stock.errors == []


@pytest.mark.parametrize("precio", ["0", "0.00", "10.00", "99999999.99"])
def test_precio_valido(contexto_app, precio):
    form = _form(precio=precio)
    form.validate()
    assert form.precio.errors == []


@pytest.mark.parametrize("stock", ["-1", "1.5", "abc", "", "1000001"])
def test_stock_invalido_produce_un_solo_error(contexto_app, stock):
    form = _form(stock=stock)
    form.validate()
    assert len(form.stock.errors) == 1


@pytest.mark.parametrize("stock", ["0", "1", "1000000"])
def test_stock_valido(contexto_app, stock):
    form = _form(stock=stock)
    form.validate()
    assert form.stock.errors == []


@pytest.mark.parametrize("nombre", ["", "   "])
def test_nombre_vacio_o_solo_espacios_produce_un_solo_error(contexto_app, nombre):
    form = _form(nombre=nombre)
    form.validate()
    assert len(form.nombre.errors) == 1


def test_formulario_completo_valido(contexto_app):
    form = _form(nombre="Teclado", precio="12.50", stock="3")
    assert form.validate() is True
