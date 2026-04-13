import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Firebase inicializado correctamente.")
        return True

    except ImportError:
        logger.error(
            "❌ firebase_admin no está instalado. "
            "Ejecuta: pip install firebase-admin"
        )
        return False
    except FileNotFoundError:
        logger.error(
            "❌ No se encontró app/core/firebase_credentials.json. "
            "Asegúrate de que el archivo de credenciales existe en esa ruta."
        )
        return False
    except Exception as e:
        logger.error(f"❌ Error inicializando Firebase: {e}")
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
        logger.info(f"✅ Notificación enviada: '{title}' → token: {token[:20]}...")
        return True

    except Exception as e:
        logger.error(f"❌ Error FCM send_notification: {e}")
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


def notify_nueva_subasta_geo(
    fcm_token: str,
    nombre_producto: str,
    ciudad: str,
    producto_id: int,
) -> None:
    """Notifica de una nueva subasta en la ciudad del usuario."""
    send_notification(
        token=fcm_token,
        title="📍 Nueva subasta cerca",
        body=f"'{nombre_producto}' en {ciudad}",
        data={"tipo": "geo", "producto_id": str(producto_id), "ciudad": ciudad},
    )