from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base, engine


async def init_db() -> None:
    """Crea todas las tablas y los índices necesarios."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Índices para optimizar consultas de pujas (HU-05)
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_pujas_producto_id "
                "ON pujas (producto_id);"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_pujas_usuario_id "
                "ON pujas (usuario_id);"
            )
        )
