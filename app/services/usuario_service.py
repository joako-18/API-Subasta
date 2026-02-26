from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse, UsuarioCreate, UsuarioUpdate


async def registrar_usuario(db: AsyncSession, data: UsuarioCreate) -> Usuario:
    """HU-U1: Crea un nuevo usuario con contraseña hasheada."""
    # Verificar email único
    result = await db.execute(select(Usuario).where(Usuario.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    usuario = Usuario(
        nombre=data.nombre,
        email=data.email,
        contrasena=hash_password(data.contrasena),
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario)
    return usuario


async def login_usuario(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Autentica un usuario y devuelve un JWT."""
    result = await db.execute(select(Usuario).where(Usuario.email == data.email))
    usuario = result.scalar_one_or_none()
    if not usuario or not verify_password(data.contrasena, usuario.contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    token = create_access_token(usuario.id)
    return TokenResponse(access_token=token)


async def actualizar_usuario(
    db: AsyncSession, usuario: Usuario, data: UsuarioUpdate
) -> Usuario:
    """HU-U3: Actualiza nombre o contraseña del usuario."""
    if data.nombre is not None:
        usuario.nombre = data.nombre
    if data.contrasena is not None:
        usuario.contrasena = hash_password(data.contrasena)
    await db.flush()
    await db.refresh(usuario)
    return usuario


async def eliminar_usuario(db: AsyncSession, usuario: Usuario) -> None:
    """HU-U4: Elimina la cuenta validando subastas activas."""
    result = await db.execute(
        select(Producto).where(
            Producto.usuario_id == usuario.id,
            Producto.status == "activo",
        )
    )
    subastas_activas = result.scalars().all()
    if subastas_activas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El usuario tiene {len(subastas_activas)} subasta(s) activa(s). "
                "Cancélalas antes de eliminar la cuenta."
            ),
        )
    await db.delete(usuario)
