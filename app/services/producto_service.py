import math
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.producto import Producto
from app.models.puja import Puja
from app.models.usuario import Usuario
from app.schemas.producto import ProductoAnalytics, ProductoDetalle, ProductoResumen, ProductoUpdate
from app.services.fcm_service import notify_superado, notify_ganador, notify_nueva_subasta_geo

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine: distancia en km entre dos coordenadas."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ─── CRUD ─────────────────────────────────────────────────────────────────────

async def crear_producto(
    db: AsyncSession,
    nombre: str,
    descripcion: str | None,
    precio_inicial: float,
    imagen_url: str | None,
    fecha_inicio: str,
    fecha_fin: str,
    usuario_id: int,
    latitud: float | None = None,
    longitud: float | None = None,
    ciudad: str | None = None,
    entrega_en_persona: bool = False,
    es_relampago: bool = False,
) -> Producto:
    """HU-P1: Registra un nuevo producto con geolocalización y modo relámpago."""
    fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
    fecha_fin_dt = datetime.fromisoformat(fecha_fin)

    if fecha_fin_dt <= fecha_inicio_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fecha_fin debe ser mayor que fecha_inicio",
        )

    # Validación extra para subastas relámpago (30 seg – 2 min)
    if es_relampago:
        duracion_seg = (fecha_fin_dt - fecha_inicio_dt).total_seconds()
        if not (30 <= duracion_seg <= 120):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las subastas relámpago deben durar entre 30 segundos y 2 minutos.",
            )

    producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio_inicial=precio_inicial,
        imagen_url=imagen_url,
        fecha_inicio=fecha_inicio_dt,
        fecha_fin=fecha_fin_dt,
        usuario_id=usuario_id,
        latitud=latitud,
        longitud=longitud,
        ciudad=ciudad,
        entrega_en_persona=entrega_en_persona,
        es_relampago=es_relampago,
    )
    db.add(producto)
    await db.flush()
    await db.refresh(producto)

    # Notificar a usuarios de la misma ciudad (si hay ciudad)
    if ciudad:
        await _notificar_usuarios_geo(db, producto)

    return producto


async def _notificar_usuarios_geo(db: AsyncSession, producto: Producto) -> None:
    """Envía FCM a usuarios con token que han pujado en productos de la misma ciudad."""
    stmt = (
        select(Usuario.fcm_token)
        .join(Producto, Producto.usuario_id == Usuario.id)
        .where(Producto.ciudad == producto.ciudad)
        .where(Usuario.id != producto.usuario_id)
        .where(Usuario.fcm_token.isnot(None))
        .distinct()
    )
    tokens = (await db.execute(stmt)).scalars().all()
    for token in tokens:
        notify_nueva_subasta_geo(
            fcm_token=token,
            nombre_producto=producto.nombre,
            ciudad=producto.ciudad or "",
            producto_id=producto.id,
        )


async def listar_productos(
    db: AsyncSession,
    ciudad: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radio_km: float | None = None,
    solo_relampago: bool = False,
    solo_entrega_persona: bool = False,
) -> list[ProductoResumen]:
    """HU-03: Lista productos con filtros de geolocalización y modo relámpago."""
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

    # Filtros SQL simples
    if ciudad:
        stmt = stmt.where(Producto.ciudad == ciudad)
    if solo_relampago:
        stmt = stmt.where(Producto.es_relampago == True)  # noqa: E712
    if solo_entrega_persona:
        stmt = stmt.where(Producto.entrega_en_persona == True)  # noqa: E712

    rows = (await db.execute(stmt)).all()
    result = []
    for producto, precio_actual in rows:
        # Filtro por radio (Python-side, Haversine)
        if lat is not None and lon is not None and radio_km is not None:
            if producto.latitud is None or producto.longitud is None:
                continue
            distancia = _distancia_km(lat, lon, float(producto.latitud), float(producto.longitud))
            if distancia > radio_km:
                continue

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

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
        latitud=float(producto.latitud) if producto.latitud else None,
        longitud=float(producto.longitud) if producto.longitud else None,
        ciudad=producto.ciudad,
        entrega_en_persona=producto.entrega_en_persona,
        es_relampago=producto.es_relampago,
    )


async def obtener_analytics(db: AsyncSession, producto_id: int) -> ProductoAnalytics:
    """HU-Analytics: historial de precios, postores únicos, min/max."""
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")

    stmt = (
        select(Puja)
        .where(Puja.producto_id == producto_id)
        .order_by(Puja.fecha.asc())
    )
    pujas = (await db.execute(stmt)).scalars().all()

    historial = [{"fecha": str(p.fecha), "cantidad": float(p.cantidad)} for p in pujas]
    postores = len({p.usuario_id for p in pujas})
    cantidades = [p.cantidad for p in pujas]

    return ProductoAnalytics(
        producto_id=producto_id,
        nombre=producto.nombre,
        historial_precios=historial,
        total_postores=postores,
        puja_inicial=producto.precio_inicial,
        puja_maxima=max(cantidades) if cantidades else None,
        puja_minima=min(cantidades) if cantidades else None,
    )


async def editar_producto(
    db: AsyncSession, producto_id: int, data: ProductoUpdate, usuario_id: int
) -> Producto:
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if producto.usuario_id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    if data.nombre is not None:
        producto.nombre = data.nombre
    if data.descripcion is not None:
        producto.descripcion = data.descripcion
    if data.imagen_url is not None:
        producto.imagen_url = data.imagen_url

    await db.flush()
    await db.refresh(producto)
    return producto


async def eliminar_producto(db: AsyncSession, producto_id: int, usuario_id: int) -> None:
    producto = await db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    if producto.usuario_id != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    hay_pujas = (
        await db.execute(
            select(func.count(Puja.id)).where(Puja.producto_id == producto_id)
        )
    ).scalar()

    if hay_pujas and hay_pujas > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El producto ya tiene pujas. No se puede eliminar.",
        )
    await db.delete(producto)