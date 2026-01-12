"""
Configuration de la base de données
SQLAlchemy avec asyncpg pour PostgreSQL asynchrone
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from typing import AsyncGenerator

from app.core.config import settings


# Configuration du moteur SQLAlchemy asynchrone
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,  # Log des requêtes SQL en mode debug
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    poolclass=QueuePool,
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base pour les modèles SQLAlchemy
Base = declarative_base()


async def init_db():
    """
    Initialise la base de données
    Note: Les tables sont créées via le script SQL init.sql sur Supabase
    Cette fonction sert principalement à vérifier la connexion
    """
    try:
        async with engine.begin() as conn:
            # Test de connexion
            await conn.execute("SELECT 1")
        print("✅ Connexion à la base de données établie")
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dépendance FastAPI pour obtenir une session de base de données

    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_context():
    """
    Context manager pour utiliser la DB en dehors de FastAPI

    Usage:
        async with get_db_context() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
