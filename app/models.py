from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    creado_en = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Producto(db.Model):
    __tablename__ = "productos"
    __table_args__ = (
        db.CheckConstraint("length(trim(nombre)) > 0", name="ck_productos_nombre_no_vacio"),
        db.CheckConstraint("precio >= 0", name="ck_productos_precio_no_negativo"),
        db.CheckConstraint("stock >= 0", name="ck_productos_stock_no_negativo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    servidor_origen = db.Column(db.String(100), nullable=False)
    servidor_actualizacion = db.Column(db.String(100), nullable=True)
    creado_en = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    actualizado_en = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": f"{self.precio:.2f}",
            "stock": self.stock,
            "servidor_origen": self.servidor_origen,
            "servidor_actualizacion": self.servidor_actualizacion,
            "creado_en": self.creado_en.isoformat(),
            "actualizado_en": self.actualizado_en.isoformat(),
        }
