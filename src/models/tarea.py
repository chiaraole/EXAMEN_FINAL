# src/models/tarea.py
from src import db
from .enums import EstadoEnum
from .dependencia import dependencia


class Tarea(db.Model):
    __tablename__ = "tarea"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String, nullable=False)
    descripcion = db.Column(db.String, nullable=False)
    estado = db.Column(
        db.Enum(EstadoEnum, name="estado_enum"),
        default=EstadoEnum.NUEVA,
        nullable=False,
    )

    # MANY-TO-MANY con sí misma
    dependencias = db.relationship(
        "Tarea",
        secondary=dependencia,
        primaryjoin=id == dependencia.c.tarea_id,
        secondaryjoin=id == dependencia.c.depende_de_id,
        backref="referenciada_por",
    )

    # ONE-TO-MANY con Asignacion
    asignaciones = db.relationship(
        "Asignacion",
        back_populates="tarea",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Tarea {self.id}:{self.nombre}>"