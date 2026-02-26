from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    precio_inicial: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="activo")
    fecha_inicio: Mapped[datetime] = mapped_column(nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(nullable=False)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )

    vendedor: Mapped["Usuario"] = relationship("Usuario", back_populates="productos")  # noqa: F821
    pujas: Mapped[list["Puja"]] = relationship(  # noqa: F821
        "Puja", back_populates="producto", cascade="all, delete-orphan"
    )
