# src/models/usuario.py
from src import db


class Usuario(db.Model):
    __tablename__ = "usuario"

    alias = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String, nullable=False)

    # hacia asignaciones
    asignaciones = db.relationship(
        "Asignacion",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Usuario {self.alias}>"