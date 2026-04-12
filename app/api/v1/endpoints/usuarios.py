from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse, UsuarioCreate, UsuarioPublico, UsuarioUpdate
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/register", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
async def registrar(data: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    """HU-U1: Registro de nuevo usuario."""
    return await usuario_service.registrar_usuario(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autenticación. Acepta fcm_token opcional para registrar el dispositivo."""
    return await usuario_service.login_usuario(db, data)


@router.get("/me", response_model=UsuarioPublico)
async def perfil(current_user: Usuario = Depends(get_current_user)):
    """HU-U2: Perfil propio."""
    return current_user


@router.put("/me", response_model=UsuarioPublico)
async def actualizar(
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-U3: Actualizar nombre, contraseña o fcm_token."""
    return await usuario_service.actualizar_usuario(db, current_user, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """HU-U4: Eliminar cuenta (bloqueado si tiene subastas activas)."""
    await usuario_service.eliminar_usuario(db, current_user)