import click

from app.extensions import db
from app.models import Usuario

CORREO_DEMO = "demo@lab07.pe"


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        """Crea el usuario de prueba. Es idempotente: se puede ejecutar varias veces."""
        existente = db.session.execute(
            db.select(Usuario).filter_by(correo=CORREO_DEMO)
        ).scalar_one_or_none()

        if existente:
            click.echo("El usuario demo ya existe; no se hizo ningún cambio.")
            return

        usuario = Usuario(nombre="Usuario Demo", correo=CORREO_DEMO)
        usuario.set_password("Demo1234!")
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuario demo creado: {CORREO_DEMO}")