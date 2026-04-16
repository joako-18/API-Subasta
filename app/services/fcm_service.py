import logging
import os
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
_CREDENTIALS_PATH = os.path.normpath(os.path.join(_SERVICES_DIR, "..", "core", "firebase_credentials.json"))

_firebase_ready = False


def _init_firebase() -> bool:
    global _firebase_ready
    if _firebase_ready:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials

        logger.info(f"Buscando credenciales Firebase en: {_CREDENTIALS_PATH}")

        if not os.path.exists(_CREDENTIALS_PATH):
            logger.error(f"❌ No se encontró el archivo de credenciales en: {_CREDENTIALS_PATH}")
            return False

        if not firebase_admin._apps:
            cred = credentials.Certificate(_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)

        _firebase_ready = True
        logger.info("✅ Firebase inicializado correctamente.")
        return True

    except ImportError:
        logger.error("❌ firebase_admin no está instalado. Ejecuta: pip install firebase-admin")
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
    if not _init_firebase():
        return False
    try:
        from firebase_admin import messaging
        msg = messaging.Message(
            data={
                "title": title,
                "body": body,
                **{str(k): str(v) for k, v in (data or {}).items()},
            },
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="outbid_channel",
                ),
            ),
        )
        messaging.send(msg)
        logger.info(f"✅ Notificación enviada: '{title}' → token: {token[:20]}...")
        return True

    except Exception as e:
        logger.error(f"❌ Error FCM send_notification: {e}")
        return False


def notify_superado(fcm_token, nombre_producto, nueva_cantidad, producto_id):
    send_notification(
        token=fcm_token,
        title="😮 ¡Te superaron!",
        body=f"Alguien pujó ${nueva_cantidad} en '{nombre_producto}'",
        data={"tipo": "superado", "producto_id": str(producto_id)},
    )


def notify_ganador(fcm_token, nombre_producto, producto_id):
    send_notification(
        token=fcm_token,
        title="🏆 ¡Ganaste!",
        body=f"Ganaste la subasta de '{nombre_producto}'",
        data={"tipo": "ganador", "producto_id": str(producto_id)},
    )


def notify_cierre_proximo(fcm_token, nombre_producto, producto_id):
    send_notification(
        token=fcm_token,
        title="⏰ Subasta terminando",
        body=f"'{nombre_producto}' cierra en 1 minuto",
        data={"tipo": "cierre_proximo", "producto_id": str(producto_id)},
    )


def notify_nueva_subasta_geo(fcm_token, nombre_producto, ciudad, producto_id):
    send_notification(
        token=fcm_token,
        title="📍 Nueva subasta cerca",
        body=f"'{nombre_producto}' en {ciudad}",
        data={"tipo": "geo", "producto_id": str(producto_id), "ciudad": ciudad},
    )