from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.puja import GanadorResponse, PujaCreate, PujaPublica
from app.services import puja_service
from app.websockets.manager import manager

router = APIRouter(prefix="/pujas", tags=["Pujas"])


@router.post("", response_model=PujaPublica, status_code=status.HTTP_201_CREATED)
async def realizar_puja(
    data: PujaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-04: Registrar una puja y notificar en tiempo real por WebSocket."""
    puja = await puja_service.realizar_puja(db, data, current_user.id)

    await manager.broadcast(
        data.producto_id,
        {
            "evento": "nueva_puja",
            "puja_id": puja.id,
            "producto_id": puja.producto_id,
            "usuario_id": puja.usuario_id,
            "nombre_postor": current_user.nombre,
            "cantidad": str(puja.cantidad),
            "fecha": str(puja.fecha),
        },
    )

    return PujaPublica(
        id=puja.id,
        producto_id=puja.producto_id,
        usuario_id=puja.usuario_id,
        nombre_postor=current_user.nombre,
        cantidad=puja.cantidad,
        fecha=puja.fecha,
    )

@router.get("/producto/{producto_id}/ganador", response_model=GanadorResponse)
async def ganador(producto_id: int, db: AsyncSession = Depends(get_db)):
    """HU-06: Obtener el ganador de la subasta finalizada."""
    return await puja_service.obtener_ganador(db, producto_id)


@router.get("/producto/{producto_id}", response_model=list[PujaPublica])
async def historial(producto_id: int, db: AsyncSession = Depends(get_db)):
    """HU-05: Historial de pujas de un producto, ordenado por fecha descendente."""
    return await puja_service.listar_pujas_producto(db, producto_id)


@router.websocket("/ws/{producto_id}")
async def websocket_subasta(websocket: WebSocket, producto_id: int):
    """
    Canal en tiempo real para una subasta.
    Los clientes se conectan y reciben actualizaciones JSON cuando
    se registra una nueva puja (broadcast desde POST /pujas).
    """
    await manager.connect(producto_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(producto_id, websocket)