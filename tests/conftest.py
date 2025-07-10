"""
Conftest global para que pytest encuentre el paquete `src`
y proporcione un cliente con una BD SQLite temporal.
"""

import sys
from pathlib import Path

# ------------------------------------------------------------------ #
# 1. Añadir la raíz del repo al PYTHONPATH, antes de importar `src`.
# ------------------------------------------------------------------ #
ROOT_DIR = Path(__file__).resolve().parents[1]          # …/examenfinal2025_01
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ------------------------------------------------------------------ #
# 2. Importar la app que YA tiene las rutas (src.controller.app)
# ------------------------------------------------------------------ #
import pytest
from src import db
import src.controller as ctrl           # ← aquí viven todos los @app.route

app = ctrl.app                           # atajo legible

# ------------------------------------------------------------------ #
# 3. Fixture `client` para cada test
# ------------------------------------------------------------------ #
@pytest.fixture(scope="function")
def client(tmp_path):
    """
    Crea una base de datos temporal por test y expone un test_client().
    """
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path}/test.db",
    )
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()