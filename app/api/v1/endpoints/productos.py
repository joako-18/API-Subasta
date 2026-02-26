from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.post("", response_model=ProductoResumen, status_code=status.HTTP_201_CREATED)
async def crear(
    data: ProductoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-P1: Publicar un nuevo producto en subasta."""
    return await producto_service.crear_producto(db, data, current_user.id)


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
