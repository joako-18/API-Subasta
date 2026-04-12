from datetime import datetime
from pydantic import BaseModel, EmailStr


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    contrasena: str


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    contrasena: str | None = None
    fcm_token: str | None = None  # actualizable desde el app al iniciar sesión


class UsuarioPublico(BaseModel):
    id: int
    nombre: str
    email: str
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str
    fcm_token: str | None = None  # enviado al hacer login para registrar el dispositivo


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"