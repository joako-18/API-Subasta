from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Puja(Base):
    __tablename__ = "pujas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    producto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    producto: Mapped["Producto"] = relationship("Producto", back_populates="pujas")
    postor: Mapped["Usuario"] = relationship("Usuario", back_populates="pujas")