"""
Endpoints REST de la Pregunta 1.
Cada ruta llama a la capa de negocio (src.data_handler) y traduce
ValueError → 422 · LookupError → 404
"""

from flask import request, jsonify
from werkzeug.exceptions import HTTPException

from src import create_app
from src.data_handler import (
    crear_usuario,
    crear_tarea,
    cambiar_estado,
    gestionar_usuario_en_tarea,
    gestionar_dependencia,
)

app = create_app()  # instancia creada por la factory --------------------------------

# --------------------------------------------------------------------- #
# 17. POST /usuarios --------------------------------------------------- #
# --------------------------------------------------------------------- #
@app.route("/usuarios", methods=["POST"])
def api_crear_usuario():
    datos = request.get_json(force=True)
    try:
        respuesta = crear_usuario(datos["contacto"], datos["nombre"])
        return jsonify(respuesta), 201
    except ValueError as e:
        return _json_error(str(e), 422)


# --------------------------------------------------------------------- #
# 18. GET /usuarios/mialias=<alias> ----------------------------------- #
# --------------------------------------------------------------------- #
@app.route("/usuarios/mialias=<alias>", methods=["GET"])
def api_usuario_con_tareas(alias):
    from src.models.usuario import Usuario
    from src.models.asignacion import Asignacion
    from src.models.tarea import Tarea

    usuario = Usuario.query.get(alias)
    if not usuario:
        return _json_error("Usuario no encontrado", 404)

    tareas = (
        Tarea.query.join(Asignacion)
        .filter(Asignacion.usuario_alias == alias)
        .all()
    )

    return jsonify(
        {
            "alias": usuario.alias,
            "nombre": usuario.nombre,
            "tareas": [
                {"id": t.id, "nombre": t.nombre, "estado": t.estado.value}
                for t in tareas
            ],
        }
    ), 200


# --------------------------------------------------------------------- #
# 19. POST /tasks ------------------------------------------------------ #
# --------------------------------------------------------------------- #
@app.route("/tasks", methods=["POST"])
def api_crear_tarea():
    datos = request.get_json(force=True)
    try:
        nueva = crear_tarea(
            datos["nombre"],
            datos["descripcion"],
            datos["usuario"],
            datos["rol"],
        )
        return jsonify(nueva), 201
    except LookupError as e:
        return _json_error(str(e), 404)
    except ValueError as e:
        return _json_error(str(e), 422)


# --------------------------------------------------------------------- #
# 20. POST /tasks/<id>  (cambio de estado) ----------------------------- #
# --------------------------------------------------------------------- #
@app.route("/tasks/<int:tarea_id>", methods=["POST"])
def api_cambiar_estado(tarea_id):
    nuevo_estado = request.get_json(force=True).get("estado")
    try:
        resp = cambiar_estado(tarea_id, nuevo_estado)
        return jsonify(resp)
    except LookupError as e:
        return _json_error(str(e), 404)
    except ValueError as e:
        return _json_error(str(e), 422)


# --------------------------------------------------------------------- #
# 21. POST /tasks/<id>/users ------------------------------------------ #
# --------------------------------------------------------------------- #
@app.route("/tasks/<int:tarea_id>/users", methods=["POST"])
def api_gestionar_usuario(tarea_id):
    d = request.get_json(force=True)
    try:
        resp = gestionar_usuario_en_tarea(
            tarea_id, d["usuario"], d["rol"], d["accion"]
        )
        return jsonify(resp)
    except LookupError as e:
        return _json_error(str(e), 404)
    except ValueError as e:
        return _json_error(str(e), 422)


# --------------------------------------------------------------------- #
# 22. POST /tasks/<id>/dependencies ----------------------------------- #
# --------------------------------------------------------------------- #
@app.route("/tasks/<int:tarea_id>/dependencies", methods=["POST"])
def api_gestionar_dependencia(tarea_id):
    d = request.get_json(force=True)
    try:
        resp = gestionar_dependencia(tarea_id, d["dependencytaskid"], d["accion"])
        return jsonify(resp)
    except LookupError as e:
        return _json_error(str(e), 404)
    except ValueError as e:
        return _json_error(str(e), 422)
    

    # en src/controller.py, al final
@app.route("/tasks/<int:tarea_id>", methods=["GET"])
def api_get_tarea(tarea_id):
    from src.models.tarea import Tarea
    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        return _json_error("Tarea no encontrada", 404)
    return jsonify({
        "id": tarea.id,
        "nombre": tarea.nombre,
        "estado": tarea.estado.value,
    })


# --------------------------------------------------------------------- #
# 23. Manejadores globales de error (404 y 422) ----------------------- #
# --------------------------------------------------------------------- #
def _json_error(msg: str, code: int):
    return jsonify({"error": msg}), code


@app.errorhandler(404)
@app.errorhandler(422)
def handler_http_error(err: HTTPException):
    # err.description viene de abort(), err.code del decorador
    return _json_error(err.description if err.description else "Not found", err.code)