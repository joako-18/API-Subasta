from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.producto import Producto
from app.models.puja import Puja
from app.models.usuario import Usuario
from app.schemas.producto import ProductoDetalle, ProductoResumen, ProductoUpdate


async def crear_producto(
    db: AsyncSession,
    nombre: str,
    descripcion: str,
    precio_inicial: float,
    imagen_url: str | None,
    fecha_inicio: str,
    fecha_fin: str,
    usuario_id: int,
) -> Producto:
    """HU-P1: Registra un nuevo producto."""
    # Las fechas llegan del app en hora de México y se guardan tal cual (naive).
    # puja_service las compara contra datetime.now(MEXICO_TZ) para consistencia.
    fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
    fecha_fin_dt = datetime.fromisoformat(fecha_fin)

    if fecha_fin_dt <= fecha_inicio_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin debe ser mayor que fecha_inicio",
        )

    producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio_inicial=precio_inicial,
        imagen_url=imagen_url,
        fecha_inicio=fecha_inicio_dt,
        fecha_fin=fecha_fin_dt,
        usuario_id=usuario_id,
    )
    db.add(producto)
    await db.flush()
    await db.refresh(producto)
    return producto


async def listar_productos(db: AsyncSession) -> list[ProductoResumen]:
    """HU-03: Lista todos los productos con su precio actual (puja más alta)."""
    max_puja = (
        select(Puja.producto_id, func.max(Puja.cantidad).label("max_cantidad"))
        .group_by(Puja.producto_id)
        .subquery()
    )
    stmt = (
        select(Producto, max_puja.c.max_cantidad)
        .outerjoin(max_puja, Producto.id == max_puja.c.producto_id)
        .order_by(Producto.id.desc())
    )
    rows = (await db.execute(stmt)).all()
    result = []
    for producto, precio_actual in rows:
        resumen = ProductoResumen.model_validate(producto)
        resumen.precio_actual = precio_actual
        result.append(resumen)
    return result


async def obtener_producto_detalle(db: AsyncSession, producto_id: int) -> ProductoDetalle:
    """HU-P2: Detalle del producto con nombre del vendedor."""
    stmt = (
        select(Producto)
        .options(selectinload(Producto.vendedor))
        .where(Producto.id == producto_id)
    )
    producto = (await db.execute(stmt)).scalar_one_or_none()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    max_cantidad = (
        await db.execute(
            select(func.max(Puja.cantidad)).where(Puja.producto_id == producto_id)
        )
    ).scalar()

    return ProductoDetalle(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio_inicial=producto.precio_inicial,
        imagen_url=producto.imagen_url,
        status=producto.status,
        fecha_inicio=producto.fecha_inicio,
        fecha_fin=producto.fecha_fin,
        usuario_id=producto.usuario_id,
        nombre_vendedor=producto.vendedor.nombre,
        precio_actual=max_cantidad,
    )


async def editar_producto(
    db: AsyncSession, producto_id: int, data: ProductoUpdate, usuario_id: int
) -> Producto:
    """HU-P3: Edita nombre/descripción."""
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )
    if producto.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        )

    if data.nombre is not None:
        producto.nombre = data.nombre
    if data.descripcion is not None:
        producto.descripcion = data.descripcion
    if data.imagen_url is not None:
        producto.imagen_url = data.imagen_url

    await db.flush()
    await db.refresh(producto)
    return producto


async def eliminar_producto(
    db: AsyncSession, producto_id: int, usuario_id: int
) -> None:
    """HU-P4: Elimina producto; bloquea si hay pujas activas."""
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )
    if producto.usuario_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        )

    hay_pujas = (
        await db.execute(
            select(func.count(Puja.id)).where(Puja.producto_id == producto_id)
        )
    ).scalar()

    if hay_pujas and hay_pujas > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El producto ya tiene pujas registradas. "
                "No se puede eliminar. Considere cancelar la subasta."
            ),
        )
    await db.delete(producto)