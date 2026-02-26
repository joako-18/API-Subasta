from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas e índices
    await init_db()
    yield
    # Shutdown: nada que limpiar (SQLAlchemy cierra el pool)


app = FastAPI(
    title="API Subastas en Tiempo Real",
    description=(
        "Backend para un sistema de subastas con autenticación JWT, "
        "gestión de productos y pujas en tiempo real vía WebSockets."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir todos los routers
app.include_router(api_router)
