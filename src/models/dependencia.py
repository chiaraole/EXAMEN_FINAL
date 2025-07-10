# src/models/dependencia.py
from src import db

dependencia = db.Table(
    "dependencia",
    db.Column("tarea_id", db.Integer, db.ForeignKey("tarea.id"), primary_key=True),
    db.Column(
        "depende_de_id",
        db.Integer,
        db.ForeignKey("tarea.id"),
        primary_key=True,
    ),
)