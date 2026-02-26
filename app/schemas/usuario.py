from datetime import datetime

from pydantic import BaseModel, EmailStr


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    contrasena: str


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    contrasena: str | None = None


class UsuarioPublico(BaseModel):
    id: int
    nombre: str
    email: str
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
