from app.models import Usuario


def test_seed_crea_usuario_demo_en_minusculas(app):
    runner = app.test_cli_runner()
    resultado = runner.invoke(args=["seed"])
    assert "creado" in resultado.output

    with app.app_context():
        usuario = Usuario.query.filter_by(correo="demo@lab07.pe").first()
        assert usuario is not None
        assert usuario.correo == usuario.correo.lower()
        assert usuario.check_password("Demo1234!")


def test_seed_es_idempotente(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["seed"])
    segundo_resultado = runner.invoke(args=["seed"])

    assert "ya existe" in segundo_resultado.output
    with app.app_context():
        assert Usuario.query.count() == 1
