# src/models/enums.py
from enum import Enum


class EstadoEnum(str, Enum):
    NUEVA = "NUEVA"
    EN_PROGRESO = "EN_PROGRESO"
    FINALIZADA = "FINALIZADA"


class RolEnum(str, Enum):
    PROGRAMADOR = "programador"
    PRUEBAS = "pruebas"
    INFRA = "infra"