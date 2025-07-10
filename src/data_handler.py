"""
Capa de servicio / lógica de negocio para la Pregunta 1.
Separa las reglas de Flask para facilitar los tests unitarios.
"""

from typing import Dict, Any, List

from src import db
from src.models.usuario import Usuario
from src.models.tarea import Tarea
from src.models.asignacion import Asignacion
from src.models.enums import EstadoEnum, RolEnum
from src.models.dependencia import dependencia


# -------------------------------------------------
# 12. crear_usuario
# -------------------------------------------------
def crear_usuario(alias: str, nombre: str) -> Dict[str, Any]:
    if Usuario.query.get(alias):
        raise ValueError("Alias ya registrado")

    nuevo = Usuario(alias=alias, nombre=nombre)
    db.session.add(nuevo)
    db.session.commit()
    return {"alias": nuevo.alias, "nombre": nuevo.nombre}


# -------------------------------------------------
# 13. crear_tarea
# -------------------------------------------------
def crear_tarea(
    nombre: str,
    descripcion: str,
    usuario_alias: str,
    rol: str,
) -> Dict[str, Any]:
    # Usuario debe existir
    usuario = Usuario.query.get(usuario_alias)
    if not usuario:
        raise LookupError("Usuario no encontrado")

    # Rol válido
    try:
        rol_enum = RolEnum(rol)
    except ValueError:
        raise ValueError("Rol inválido")

    tarea = Tarea(
        nombre=nombre,
        descripcion=descripcion,
        estado=EstadoEnum.NUEVA,
    )
    db.session.add(tarea)
    db.session.flush()  # para obtener tarea.id

    asignacion = Asignacion(
        usuario_alias=usuario.alias,
        tarea_id=tarea.id,
        rol=rol_enum,
    )
    db.session.add(asignacion)
    db.session.commit()

    return {"id": tarea.id}


# -------------------------------------------------
# 14. cambiar_estado
# -------------------------------------------------
_TRANSICIONES_VALIDAS = {
    (EstadoEnum.NUEVA, EstadoEnum.EN_PROGRESO),
    (EstadoEnum.EN_PROGRESO, EstadoEnum.FINALIZADA),
    (EstadoEnum.EN_PROGRESO, EstadoEnum.NUEVA),
}


def cambiar_estado(tarea_id: int, nuevo_estado: str) -> Dict[str, Any]:
    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        raise LookupError("Tarea no encontrada")

    try:
        nuevo_enum = EstadoEnum(nuevo_estado)
    except ValueError:
        raise ValueError("Estado inválido")

    if (tarea.estado, nuevo_enum) not in _TRANSICIONES_VALIDAS:
        raise ValueError("Transición de estado no permitida")

    # Si quiere finalizar, todas las dependencias deben estar finalizadas
    if nuevo_enum == EstadoEnum.FINALIZADA:
        pendientes = [
            dep.id for dep in tarea.dependencias if dep.estado != EstadoEnum.FINALIZADA
        ]
        if pendientes:
            raise ValueError(
                f"Dependencias no finalizadas: {pendientes}"
            )

    tarea.estado = nuevo_enum
    db.session.commit()
    return {"id": tarea.id, "estado": tarea.estado.value}


# -------------------------------------------------
# 15. gestionar_usuario_en_tarea
# -------------------------------------------------
def gestionar_usuario_en_tarea(
    tarea_id: int,
    usuario_alias: str,
    rol: str,
    accion: str,
) -> Dict[str, Any]:
    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        raise LookupError("Tarea no encontrada")

    usuario = Usuario.query.get(usuario_alias)
    if not usuario:
        raise LookupError("Usuario no encontrado")

    try:
        rol_enum = RolEnum(rol)
    except ValueError:
        raise ValueError("Rol inválido")

    existe = Asignacion.query.get((usuario_alias, tarea_id, rol_enum))

    if accion == "adicionar":
        if existe:
            raise ValueError("Asignación ya existe")
        db.session.add(
            Asignacion(
                usuario_alias=usuario_alias,
                tarea_id=tarea_id,
                rol=rol_enum,
            )
        )
    elif accion == "remover":
        if not existe:
            raise ValueError("Asignación no encontrada")
        # Evitar dejar la tarea sin usuarios
        if len(tarea.asignaciones) == 1:
            raise ValueError("La tarea debe tener al menos un usuario asignado")
        db.session.delete(existe)
    else:
        raise ValueError("Acción inválida (use adicionar/remover)")

    db.session.commit()
    return {"tarea_id": tarea_id, "usuarios": _usuarios_de_tarea(tarea)}


def _usuarios_de_tarea(t: Tarea) -> List[Dict[str, str]]:
    return [
        {"alias": a.usuario_alias, "rol": a.rol.value} for a in t.asignaciones
    ]


# -------------------------------------------------
# 16. gestionar_dependencia
# -------------------------------------------------
def gestionar_dependencia(
    tarea_id: int,
    depende_de_id: int,
    accion: str,
) -> Dict[str, Any]:
    if tarea_id == depende_de_id:
        raise ValueError("Una tarea no puede depender de sí misma")

    tarea = Tarea.query.get(tarea_id)
    depende_de = Tarea.query.get(depende_de_id)
    if not tarea or not depende_de:
        raise LookupError("Alguna de las tareas no existe")

    # Detectar ciclos simples: depende_de ya depende (directa o indirectamente) de tarea
    if _hay_ciclo(tarea, depende_de):
        raise ValueError("La dependencia crearía un ciclo")

    conn = db.engine.connect()
    trans = conn.begin()

    try:
        if accion == "adicionar":
            # ¿ya existe?
            existe = conn.execute(
                dependencia.select().where(
                    (dependencia.c.tarea_id == tarea_id)
                    & (dependencia.c.depende_de_id == depende_de_id)
                )
            ).fetchone()
            if existe:
                raise ValueError("La dependencia ya existe")

            conn.execute(
                dependencia.insert().values(
                    tarea_id=tarea_id, depende_de_id=depende_de_id
                )
            )
        elif accion == "remover":
            res = conn.execute(
                dependencia.delete().where(
                    (dependencia.c.tarea_id == tarea_id)
                    & (dependencia.c.depende_de_id == depende_de_id)
                )
            )
            if res.rowcount == 0:
                raise ValueError("La dependencia no existe")
        else:
            raise ValueError("Acción inválida (use adicionar/remover)")

        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()

    return {"tarea_id": tarea_id, "dependencias": [d.id for d in tarea.dependencias]}


def _hay_ciclo(tarea: Tarea, depende_de: Tarea) -> bool:
    """DFS simple para detectar ciclo tarea ← … ← depende_de ← tarea"""
    stack = [depende_de]
    visitados = set()
    while stack:
        actual = stack.pop()
        if actual.id == tarea.id:
            return True
        visitados.add(actual.id)
        stack.extend(
            d for d in actual.dependencias if d.id not in visitados
        )
    return False