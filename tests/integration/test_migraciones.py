from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.extensions import db


def test_migracion_coincide_con_los_modelos(app):
    with app.app_context():
        conexion = db.engine.connect()
        try:
            contexto = MigrationContext.configure(conexion)
            diferencias = compare_metadata(contexto, db.metadata)
        finally:
            conexion.close()
    assert diferencias == []
