from fastapi import APIRouter
from app.api.v1.endpoints import productos, pujas, usuarios

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(usuarios.router)
api_router.include_router(productos.router)
api_router.include_router(pujas.router)