import click

from app.extensions import db
from app.models import Usuario

CORREO_SEED = "demo@lab07.pe"
NOMBRE_SEED = "Usuario Demo"
PASSWORD_SEED = "Demo1234!"


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        """Crea el usuario de demostración si no existe."""
        if Usuario.query.filter_by(correo=CORREO_SEED).first() is not None:
            click.echo(f"El usuario {CORREO_SEED} ya existe; no se hace nada.")
            return

        usuario = Usuario(nombre=NOMBRE_SEED, correo=CORREO_SEED)
        usuario.set_password(PASSWORD_SEED)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuario {CORREO_SEED} creado.")
