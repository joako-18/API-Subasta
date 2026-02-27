from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os, uuid, shutil

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.producto import (
    ProductoCreate,
    ProductoDetalle,
    ProductoResumen,
    ProductoUpdate,
)
from app.services import producto_service

router = APIRouter(prefix="/productos", tags=["Productos"])

UPLOAD_DIR = "static/imagenes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("", status_code=201)
async def crear_producto(
    nombre: str = Form(...),
    descripcion: str = Form(...),
    precio_inicial: float = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    imagen: UploadFile = File(None),  # opcional
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    imagen_url = None
    if imagen and imagen.filename:
        ext = imagen.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"{UPLOAD_DIR}/{filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(imagen.file, f)
        imagen_url = f"http://3.211.145.251:8000/static/imagenes/{filename}"

    return await producto_service.crear_producto(
        db=db,
        nombre=nombre,
        descripcion=descripcion,
        precio_inicial=precio_inicial,
        imagen_url=imagen_url,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        usuario_id=current_user.id
    )


@router.get("", response_model=list[ProductoResumen])
async def listar(db: AsyncSession = Depends(get_db)):
    """HU-03: Listar todos los productos con precio actual."""
    return await producto_service.listar_productos(db)


@router.get("/{producto_id}", response_model=ProductoDetalle)
async def detalle(producto_id: int, db: AsyncSession = Depends(get_db)):
    """HU-P2: Detalle del producto con nombre del vendedor."""
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
