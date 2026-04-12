from sqlalchemy import text
from app.db.database import Base, engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Índices para pujas
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_pujas_producto_id ON pujas (producto_id);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_pujas_usuario_id ON pujas (usuario_id);"
        ))
        # Índices para geolocalización — en MySQL hay que verificar antes
        await conn.execute(text("""
            SELECT IF(
                EXISTS(
                    SELECT 1 FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                    AND table_name = 'productos'
                    AND index_name = 'idx_productos_ciudad'
                ),
                'SELECT 1',
                'CREATE INDEX idx_productos_ciudad ON productos (ciudad(255))'
            ) INTO @sql;
        """))
        await conn.execute(text("PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;"))

        await conn.execute(text("""
            SELECT IF(
                EXISTS(
                    SELECT 1 FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                    AND table_name = 'productos'
                    AND index_name = 'idx_productos_relampago'
                ),
                'SELECT 1',
                'CREATE INDEX idx_productos_relampago ON productos (es_relampago)'
            ) INTO @sql;
        """))
        await conn.execute(text("PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;"))