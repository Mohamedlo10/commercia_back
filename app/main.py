"""
Commercia Backend API - Point d'entrée principal
FastAPI application avec PostgreSQL via SQLAlchemy et asyncpg
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.database import engine, init_db, check_db_connection
from app.api.v1.api import api_router


# Lifespan context manager pour gérer le démarrage et l'arrêt
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application"""
    # Démarrage
    print("🚀 Démarrage de l'application Commercia...")
    await init_db()
    print("✅ Base de données initialisée")
    yield
    # Arrêt
    print("⏹️  Arrêt de l'application...")
    await engine.dispose()
    print("✅ Connexions fermées")


# Créer l'application FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Backend pour la gestion commerciale Commercia",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware pour logger les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log toutes les requêtes avec leur temps d'exécution"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"📨 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response


# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gère toutes les exceptions non capturées"""
    print(f"❌ Erreur non gérée: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Une erreur interne s'est produite",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# Routes de santé
@app.get("/health", tags=["Health"])
async def health_check():
    """Vérification de l'état de l'API (ne vérifie pas la DB)"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Vérification complète incluant la base de données"""
    db_connected = await check_db_connection()
    return {
        "status": "ready" if db_connected else "degraded",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "database": "connected" if db_connected else "disconnected"
    }


@app.get("/", tags=["Root"])
async def root():
    """Route racine"""
    return {
        "message": "Bienvenue sur l'API Commercia",
        "docs": "/api/docs",
        "health": "/health"
    }


# Inclure tous les routers API
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
