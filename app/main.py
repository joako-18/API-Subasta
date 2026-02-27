import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos para imágenes
os.makedirs("static/imagenes", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router)