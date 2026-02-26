from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    contrasena: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    productos: Mapped[list["Producto"]] = relationship(
        "Producto", back_populates="vendedor", cascade="all, delete-orphan"
    )
    pujas: Mapped[list["Puja"]] = relationship(
        "Puja", back_populates="postor", cascade="all, delete-orphan"
    )