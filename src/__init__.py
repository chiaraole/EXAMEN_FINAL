"""
Fábrica de la aplicación Flask y configuración de SQLAlchemy.
Evita import circular: los modelos se importan DENTRO de create_app().
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # objeto global reutilizable


def create_app() -> Flask:
    """Construye y devuelve la aplicación principal."""
    app = Flask(__name__)

    # ---------- Config Básica ----------
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dev.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializa la BD
    db.init_app(app)

    # ------ Importa modelos una vez que db está listo ------
    with app.app_context():
        from src.models import usuario, tarea, asignacion, dependencia  # noqa: F401

    return app