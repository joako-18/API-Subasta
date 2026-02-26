# 🏗️ Arquitectura del Proyecto - API Subastas en Tiempo Real

## Estructura de Carpetas

```
subasta-api/
├── app/
│   ├── main.py                        # Entry point FastAPI
│   ├── api/
│   │   └── v1/
│   │       ├── router.py              # Router principal v1
│   │       └── endpoints/
│   │           ├── usuarios.py        # HU-U1, U2, U3, U4
│   │           ├── productos.py       # HU-P1, P2, P3, P4, HU-03
│   │           └── pujas.py          # HU-04, HU-05, HU-06
│   ├── core/
│   │   ├── config.py                  # Variables de entorno
│   │   ├── security.py               # JWT + hashing de contraseñas
│   │   └── dependencies.py           # Inyección de dependencias
│   ├── db/
│   │   ├── database.py               # Conexión SQLAlchemy + AsyncPG
│   │   └── init_db.py                # Inicialización de tablas e índices
│   ├── models/
│   │   ├── usuario.py                # Modelo ORM usuarios
│   │   ├── producto.py               # Modelo ORM productos
│   │   └── puja.py                   # Modelo ORM pujas
│   ├── schemas/
│   │   ├── usuario.py                # Pydantic schemas usuarios
│   │   ├── producto.py               # Pydantic schemas productos
│   │   └── puja.py                   # Pydantic schemas pujas
│   ├── services/
│   │   ├── usuario_service.py        # Lógica de negocio usuarios
│   │   ├── producto_service.py       # Lógica de negocio productos
│   │   └── puja_service.py          # Lógica de negocio pujas + ganador
│   └── websockets/
│       └── manager.py                # WebSocket ConnectionManager
├── .env.example                      # Variables de entorno ejemplo
├── requirements.txt                  # Dependencias
└── ESTRUCTURA.md                     # Este archivo
```

## Capas de la Arquitectura

```
┌─────────────────────────────────────────┐
│           API Layer (Endpoints)         │  ← HTTP + WebSocket handlers
│        api/v1/endpoints/*.py            │
├─────────────────────────────────────────┤
│           Service Layer                 │  ← Lógica de negocio y reglas
│          services/*.py                  │
├─────────────────────────────────────────┤
│       Repository / ORM Layer            │  ← Acceso a datos vía SQLAlchemy
│       models/*.py + db/database.py      │
├─────────────────────────────────────────┤
│           Database (PostgreSQL)         │
└─────────────────────────────────────────┘
```

## Flujo de una Puja en Tiempo Real

```
Cliente A  ──POST /pujas──►  PujasEndpoint
                                   │
                             PujaService
                           (valida monto y fecha)
                                   │
                             DB (INSERT puja)
                                   │
                          WebSocket Manager
                         broadcast a todos ◄──── Cliente B, C, D...
```

## Historias de Usuario Cubiertas

| HU      | Endpoint                          | Método   |
|---------|-----------------------------------|----------|
| HU-U1   | /api/v1/usuarios/register         | POST     |
| HU-U2   | /api/v1/usuarios/me               | GET      |
| HU-U3   | /api/v1/usuarios/me               | PUT      |
| HU-U4   | /api/v1/usuarios/me               | DELETE   |
| HU-P1   | /api/v1/productos                 | POST     |
| HU-P2   | /api/v1/productos/{id}            | GET      |
| HU-P3   | /api/v1/productos/{id}            | PUT      |
| HU-P4   | /api/v1/productos/{id}            | DELETE   |
| HU-03   | /api/v1/productos                 | GET      |
| HU-04   | /api/v1/pujas                     | POST     |
| HU-05   | /api/v1/pujas/producto/{id}       | GET      |
| HU-06   | /api/v1/pujas/producto/{id}/ganador| GET     |
| RT      | /ws/{producto_id}                 | WebSocket|
