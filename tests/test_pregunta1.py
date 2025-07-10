import json

# Pytest detecta automáticamente el fixture `client` definido en conftest.py
# Solo necesitamos importarlo para que el editor no marque un warning.
from tests.conftest import client  # noqa: F401


# ---------- helper -------------------------------------------------- #
def _post(client, url, payload, code):
    resp = client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == code, resp.get_json()
    return resp.get_json()


# ---------- CASOS: USUARIOS ---------------------------------------- #
def test_crear_usuario_y_duplicado(client):
    _post(client, "/usuarios", {"contacto": "eva", "nombre": "Eva"}, 201)
    dup = _post(client, "/usuarios", {"contacto": "eva", "nombre": "Otra"}, 422)
    assert dup["error"] == "Alias ya registrado"


def test_get_usuario_sin_tareas_y_404(client):
    _post(client, "/usuarios", {"contacto": "eva", "nombre": "Eva"}, 201)
    ok = client.get("/usuarios/mialias=eva")
    assert ok.status_code == 200 and ok.get_json()["tareas"] == []
    assert client.get("/usuarios/mialias=ghost").status_code == 404


# ---------- CASOS: TAREAS ------------------------------------------ #
def test_crear_tarea_con_usuario_y_sin_usuario(client):
    _post(client, "/usuarios", {"contacto": "eva", "nombre": "Eva"}, 201)
    res = _post(
        client,
        "/tasks",
        {
            "nombre": "Integrar API",
            "descripcion": "Backend",
            "usuario": "eva",
            "rol": "programador",
        },
        201,
    )
    assert "id" in res
    _post(
        client,
        "/tasks",
        {
            "nombre": "Bad",
            "descripcion": "...",
            "usuario": "ghost",
            "rol": "programador",
        },
        404,
    )


# ---------- CASOS: ESTADOS ----------------------------------------- #
def test_transiciones_estado_validas_e_invalidas(client):
    _post(client, "/usuarios", {"contacto": "eva", "nombre": "Eva"}, 201)
    tid = _post(
        client,
        "/tasks",
        {"nombre": "A", "descripcion": "d", "usuario": "eva", "rol": "programador"},
        201,
    )["id"]

    _post(client, f"/tasks/{tid}", {"estado": "EN_PROGRESO"}, 200)   # NUEVA → EN_PROGRESO
    _post(client, f"/tasks/{tid}", {"estado": "FINALIZADA"}, 200)    # EN_PROGRESO → FINALIZADA
    _post(client, f"/tasks/{tid}", {"estado": "NUEVA"}, 422)         # inválida
    _post(client, "/tasks/999", {"estado": "EN_PROGRESO"}, 404)      # inexistente


# ---------- CASOS: ASIGNACIONES ------------------------------------ #
def test_adicionar_remover_usuario_en_tarea(client):
    for alias in ("eva", "max"):
        _post(client, "/usuarios", {"contacto": alias, "nombre": alias}, 201)
    tid = _post(
        client,
        "/tasks",
        {"nombre": "B", "descripcion": "d", "usuario": "eva", "rol": "programador"},
        201,
    )["id"]

    _post(client, f"/tasks/{tid}/users",
          {"usuario": "max", "rol": "pruebas", "accion": "adicionar"}, 200)  # add
    _post(client, f"/tasks/{tid}/users",
          {"usuario": "max", "rol": "pruebas", "accion": "adicionar"}, 422)  # duplicado
    _post(client, f"/tasks/{tid}/users",
          {"usuario": "max", "rol": "pruebas", "accion": "remover"}, 200)    # remove
    _post(client, f"/tasks/{tid}/users",
          {"usuario": "eva", "rol": "programador", "accion": "remover"}, 422)  # mínimo 1


# ---------- CASOS: DEPENDENCIAS ------------------------------------ #
def test_dependencias_ok_duplicado_ciclo_self(client):
    _post(client, "/usuarios", {"contacto": "eva", "nombre": "Eva"}, 201)
    t1 = _post(
        client,
        "/tasks",
        {"nombre": "C1", "descripcion": ".", "usuario": "eva", "rol": "programador"},
        201,
    )["id"]
    t2 = _post(
        client,
        "/tasks",
        {"nombre": "C2", "descripcion": ".", "usuario": "eva", "rol": "programador"},
        201,
    )["id"]

    _post(client, f"/tasks/{t2}/dependencies",
          {"dependencytaskid": t1, "accion": "adicionar"}, 200)   # ok
    _post(client, f"/tasks/{t2}/dependencies",
          {"dependencytaskid": t1, "accion": "adicionar"}, 422)   # duplicado
    _post(client, f"/tasks/{t1}/dependencies",
          {"dependencytaskid": t1, "accion": "adicionar"}, 422)   # self
    _post(client, f"/tasks/{t1}/dependencies",
          {"dependencytaskid": t2, "accion": "adicionar"}, 422)   # ciclo
    _post(client, f"/tasks/{t1}/dependencies",
          {"dependencytaskid": 999, "accion": "adicionar"}, 404)  # inexistente