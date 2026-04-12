from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.producto import Producto
from app.models.puja import Puja
from app.models.usuario import Usuario
from app.schemas.puja import GanadorResponse, PujaCreate, PujaPublica
from app.services.fcm_service import notify_superado, notify_ganador
MEXICO_TZ = timezone(timedelta(hours=-6))


def _now_mexico() -> datetime:
    return datetime.now(MEXICO_TZ).replace(tzinfo=None)


def _as_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(MEXICO_TZ).replace(tzinfo=None)
    return dt


async def realizar_puja(db: AsyncSession, data: PujaCreate, usuario_id: int) -> Puja:
    """HU-04: Registra una puja y lanza FCM al postor anterior si fue superado."""
    stmt = (
        select(Producto)
        .options(selectinload(Producto.pujas))
        .where(Producto.id == data.producto_id)
    )
    producto = (await db.execute(stmt)).scalar_one_or_none()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    ahora = _now_mexico()
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

    # Puja máxima actual y quién la tiene
    stmt_max = (
        select(Puja)
        .where(Puja.producto_id == data.producto_id)
        .order_by(Puja.cantidad.desc())
        .limit(1)
    )
    puja_lider = (await db.execute(stmt_max)).scalar_one_or_none()
    precio_base = puja_lider.cantidad if puja_lider else producto.precio_inicial

    if data.cantidad <= precio_base:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La puja debe ser mayor a {precio_base}",
        )

    puja = Puja(producto_id=data.producto_id, usuario_id=usuario_id, cantidad=data.cantidad)
    db.add(puja)
    await db.flush()
    await db.refresh(puja, ["postor"])

    # Notificar al postor anterior que fue superado (si es distinto al actual)
    if puja_lider and puja_lider.usuario_id != usuario_id:
        stmt_token = select(Usuario.fcm_token).where(Usuario.id == puja_lider.usuario_id)
        token = (await db.execute(stmt_token)).scalar_one_or_none()
        if token:
            notify_superado(
                fcm_token=token,
                nombre_producto=producto.nombre,
                nueva_cantidad=str(data.cantidad),
                producto_id=producto.id,
            )

    return puja


async def listar_pujas_producto(db: AsyncSession, producto_id: int) -> list[PujaPublica]:
    """HU-05: Historial de pujas, orden descendente."""
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


async def obtener_ganador(db: AsyncSession, producto_id: int) -> GanadorResponse:
    """HU-06: Ganador de la subasta finalizada. Envía FCM al ganador."""
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    ahora = _now_mexico()
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

    # FCM al ganador
    if puja_ganadora.postor.fcm_token:
        notify_ganador(
            fcm_token=puja_ganadora.postor.fcm_token,
            nombre_producto=producto.nombre,
            producto_id=producto_id,
        )

    return GanadorResponse(
        producto_id=producto_id,
        usuario_id=puja_ganadora.usuario_id,
        nombre_ganador=puja_ganadora.postor.nombre,
        cantidad_ganadora=puja_ganadora.cantidad,
        fecha=puja_ganadora.fecha,
    )