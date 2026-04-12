import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Inicialización lazy de firebase-admin para no romper el arranque si no está configurado
_firebase_ready = False


def _init_firebase() -> bool:
    global _firebase_ready
    if _firebase_ready:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            cred = credentials.Certificate("app/core/firebase_credentials.json")
            firebase_admin.initialize_app(cred)
        _firebase_ready = True
        return True
    except Exception as e:
        logger.warning(f"Firebase no inicializado (notificaciones deshabilitadas): {e}")
        return False


def send_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Envía una notificación push a un dispositivo.
    Retorna True si fue enviada, False si FCM no está configurado o falla.
    """
    if not _init_firebase():
        return False
    try:
        from firebase_admin import messaging
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},
            token=token,
            android=messaging.AndroidConfig(priority="high"),
        )
        messaging.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error FCM send_notification: {e}")
        return False


def notify_superado(
    fcm_token: str,
    nombre_producto: str,
    nueva_cantidad: str,
    producto_id: int,
) -> None:
    """Notifica al postor que fue superado."""
    send_notification(
        token=fcm_token,
        title="😮 ¡Te superaron!",
        body=f"Alguien pujó ${nueva_cantidad} en '{nombre_producto}'",
        data={"tipo": "superado", "producto_id": str(producto_id)},
    )


def notify_ganador(fcm_token: str, nombre_producto: str, producto_id: int) -> None:
    """Notifica al ganador de la subasta."""
    send_notification(
        token=fcm_token,
        title="🏆 ¡Ganaste!",
        body=f"Ganaste la subasta de '{nombre_producto}'",
        data={"tipo": "ganador", "producto_id": str(producto_id)},
    )


def notify_cierre_proximo(fcm_token: str, nombre_producto: str, producto_id: int) -> None:
    """Notifica que la subasta cierra en 1 minuto."""
    send_notification(
        token=fcm_token,
        title="⏰ Subasta terminando",
        body=f"'{nombre_producto}' cierra en 1 minuto",
        data={"tipo": "cierre_proximo", "producto_id": str(producto_id)},
    )


def notify_nueva_subasta_geo(fcm_token: str, nombre_producto: str, ciudad: str, producto_id: int) -> None:
    """Notifica de una nueva subasta en la ciudad del usuario."""
    send_notification(
        token=fcm_token,
        title="📍 Nueva subasta cerca",
        body=f"'{nombre_producto}' en {ciudad}",
        data={"tipo": "geo", "producto_id": str(producto_id), "ciudad": ciudad},
    )