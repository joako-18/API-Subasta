from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.producto import Producto
from app.models.puja import Puja
from app.schemas.puja import GanadorResponse, PujaCreate, PujaPublica


def _naive_utc_now() -> datetime:
    """Devuelve datetime UTC sin timezone info (compatible con MariaDB)."""
    return datetime.utcnow()


def _as_naive(dt: datetime) -> datetime:
    """Convierte a naive datetime para comparar con valores de MariaDB."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def realizar_puja(
    db: AsyncSession, data: PujaCreate, usuario_id: int
) -> Puja:
    """
    HU-04: Registra una puja validando:
    - El producto existe y está activo.
    - La puja es mayor a la más alta actual.
    - Está dentro del rango de fecha_inicio / fecha_fin.
    """
    stmt = (
        select(Producto)
        .options(selectinload(Producto.pujas))
        .where(Producto.id == data.producto_id)
    )
    producto = (await db.execute(stmt)).scalar_one_or_none()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    ahora = _naive_utc_now()

    # HU-06: bloquear si fecha_fin ya pasó
    if ahora > _as_naive(producto.fecha_fin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La subasta ha finalizado. No se aceptan más pujas.",
        )

    if ahora < _as_naive(producto.fecha_inicio):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La subasta aún no ha comenzado.",
        )

    # Validar que la puja supera la más alta actual
    max_cantidad = (
        await db.execute(
            select(func.max(Puja.cantidad)).where(Puja.producto_id == data.producto_id)
        )
    ).scalar()

    precio_base = max_cantidad if max_cantidad is not None else producto.precio_inicial
    if data.cantidad <= precio_base:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La puja debe ser mayor a {precio_base}",
        )

    puja = Puja(
        producto_id=data.producto_id,
        usuario_id=usuario_id,
        cantidad=data.cantidad,
    )
    db.add(puja)
    await db.flush()
    await db.refresh(puja, ["postor"])
    return puja


async def listar_pujas_producto(
    db: AsyncSession, producto_id: int
) -> list[PujaPublica]:
    """HU-05: Historial de pujas de un producto, orden descendente con nombre del postor."""
    stmt = (
        select(Puja)
        .options(selectinload(Puja.postor))
        .where(Puja.producto_id == producto_id)
        .order_by(Puja.fecha.desc())
    )
    pujas = (await db.execute(stmt)).scalars().all()
    return [
        PujaPublica(
            id=p.id,
            producto_id=p.producto_id,
            usuario_id=p.usuario_id,
            nombre_postor=p.postor.nombre,
            cantidad=p.cantidad,
            fecha=p.fecha,
        )
        for p in pujas
    ]


async def obtener_ganador(
    db: AsyncSession, producto_id: int
) -> GanadorResponse:
    """HU-06: Identifica la puja ganadora una vez finalizada la subasta."""
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    ahora = _naive_utc_now()
    if ahora <= _as_naive(producto.fecha_fin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La subasta aún no ha finalizado.",
        )

    stmt = (
        select(Puja)
        .options(selectinload(Puja.postor))
        .where(Puja.producto_id == producto_id)
        .order_by(Puja.cantidad.desc())
        .limit(1)
    )
    puja_ganadora = (await db.execute(stmt)).scalar_one_or_none()
    if not puja_ganadora:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay pujas registradas para este producto.",
        )

    return GanadorResponse(
        producto_id=producto_id,
        usuario_id=puja_ganadora.usuario_id,
        nombre_ganador=puja_ganadora.postor.nombre,
        cantidad_ganadora=puja_ganadora.cantidad,
        fecha=puja_ganadora.fecha,
    )