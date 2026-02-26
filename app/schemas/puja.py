from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PujaCreate(BaseModel):
    producto_id: int
    cantidad: Decimal


class PujaPublica(BaseModel):
    id: int
    producto_id: int
    usuario_id: int
    nombre_postor: str
    cantidad: Decimal
    fecha: datetime

    model_config = {"from_attributes": True}


class GanadorResponse(BaseModel):
    producto_id: int
    usuario_id: int
    nombre_ganador: str
    cantidad_ganadora: Decimal
    fecha: datetime
