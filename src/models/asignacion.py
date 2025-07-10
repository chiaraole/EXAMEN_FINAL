# src/models/asignacion.py
from src import db
from .enums import RolEnum


class Asignacion(db.Model):
    __tablename__ = "asignacion"

    usuario_alias = db.Column(
        db.String,
        db.ForeignKey("usuario.alias"),
        primary_key=True,
    )
    tarea_id = db.Column(
        db.Integer,
        db.ForeignKey("tarea.id"),
        primary_key=True,
    )
    rol = db.Column(
        db.Enum(RolEnum, name="rol_enum"),
        nullable=False,
        primary_key=True,
    )

    # relaciones inversas
    usuario = db.relationship("Usuario", back_populates="asignaciones")
    tarea = db.relationship("Tarea", back_populates="asignaciones")

    def __repr__(self):
        return f"<Asignacion {self.usuario_alias}-{self.tarea_id}-{self.rol}>"