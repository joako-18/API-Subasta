import os
import uuid
import shutil
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.producto import ProductoAnalytics, ProductoDetalle, ProductoResumen, ProductoUpdate
from app.services import producto_service

router = APIRouter(prefix="/productos", tags=["Productos"])

UPLOAD_DIR = "static/imagenes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
BASE_URL = "http://3.211.145.251:8000"


@router.post("", status_code=201)
async def crear_producto(
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio_inicial: float = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    imagen: UploadFile = File(None),
    # Geolocalización (opcionales)
    latitud: float | None = Form(None),
    longitud: float | None = Form(None),
    ciudad: str | None = Form(None),
    entrega_en_persona: bool = Form(False),
    # Modo relámpago
    es_relampago: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-P1: Crea producto con geolocalización y/o modo relámpago."""
    imagen_url = None
    if imagen and imagen.filename:
        ext = imagen.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"{UPLOAD_DIR}/{filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(imagen.file, f)
        imagen_url = f"{BASE_URL}/static/imagenes/{filename}"

    return await producto_service.crear_producto(
        db=db,
        nombre=nombre,
        descripcion=descripcion,
        precio_inicial=precio_inicial,
        imagen_url=imagen_url,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        usuario_id=current_user.id,
        latitud=latitud,
        longitud=longitud,
        ciudad=ciudad,
        entrega_en_persona=entrega_en_persona,
        es_relampago=es_relampago,
    )


@router.get("", response_model=list[ProductoResumen])
async def listar(
    db: AsyncSession = Depends(get_db),
    # Filtros de geolocalización
    ciudad: str | None = Query(None, description="Filtrar por ciudad exacta"),
    lat: float | None = Query(None, description="Latitud del usuario"),
    lon: float | None = Query(None, description="Longitud del usuario"),
    radio_km: float | None = Query(None, description="Radio de búsqueda en km"),
    # Filtros de tipo
    solo_relampago: bool = Query(False, description="Solo subastas relámpago"),
    solo_entrega_persona: bool = Query(False, description="Solo con entrega en persona"),
):
    """HU-03: Lista productos con filtros opcionales de geo, relámpago y entrega."""
    return await producto_service.listar_productos(
        db,
        ciudad=ciudad,
        lat=lat,
        lon=lon,
        radio_km=radio_km,
        solo_relampago=solo_relampago,
        solo_entrega_persona=solo_entrega_persona,
    )


@router.get("/{producto_id}/analytics", response_model=ProductoAnalytics)
async def analytics(producto_id: int, db: AsyncSession = Depends(get_db)):
    """HU-Analytics: Historial de precios y estadísticas de la subasta."""
    return await producto_service.obtener_analytics(db, producto_id)


@router.get("/{producto_id}", response_model=ProductoDetalle)
async def detalle(producto_id: int, db: AsyncSession = Depends(get_db)):
    """HU-P2: Detalle del producto."""
    return await producto_service.obtener_producto_detalle(db, producto_id)


@router.put("/{producto_id}", response_model=ProductoResumen)
async def editar(
    producto_id: int,
    data: ProductoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-P3: Editar producto (solo el creador)."""
    return await producto_service.editar_producto(db, producto_id, data, current_user.id)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(
    producto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-P4: Retirar producto (bloqueado si tiene pujas)."""
    await producto_service.eliminar_producto(db, producto_id, current_user.id)