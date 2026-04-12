from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator


class ProductoCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    precio_inicial: Decimal
    imagen_url: str | None = None
    fecha_inicio: datetime
    fecha_fin: datetime
    # Geolocalización (opcionales)
    latitud: float | None = None
    longitud: float | None = None
    ciudad: str | None = None
    entrega_en_persona: bool = False
    # Relámpago
    es_relampago: bool = False

    @field_validator("precio_inicial")
    @classmethod
    def precio_no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El precio inicial no puede ser negativo")
        return v


class ProductoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    imagen_url: str | None = None


class ProductoResumen(BaseModel):
    """Lista de productos con precio actual (HU-03)."""
    id: int
    nombre: str
    descripcion: str | None
    precio_inicial: Decimal
    imagen_url: str | None
    status: str
    fecha_inicio: datetime
    fecha_fin: datetime
    precio_actual: Decimal | None = None
    # Geolocalización
    latitud: float | None = None
    longitud: float | None = None
    ciudad: str | None = None
    entrega_en_persona: bool = False
    # Relámpago
    es_relampago: bool = False

    model_config = {"from_attributes": True}


class ProductoDetalle(ProductoResumen):
    """Detalle con nombre del vendedor (HU-P2)."""
    nombre_vendedor: str
    usuario_id: int


class ProductoAnalytics(BaseModel):
    """Datos de analítica para gráficas."""
    producto_id: int
    nombre: str
    historial_precios: list[dict]   # [{fecha, cantidad}]
    total_postores: int
    puja_inicial: Decimal
    puja_maxima: Decimal | None
    puja_minima: Decimal | None