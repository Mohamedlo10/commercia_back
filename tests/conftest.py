"""
Configuration pytest
Fixtures partagées pour les tests
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# Charger les variables d'environnement
load_dotenv()

# Utiliser la DB de production depuis .env (convertir postgresql:// en postgresql+asyncpg://)
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    TEST_DATABASE_URL = DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """Crée un event loop pour les tests asynchrones"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Crée un moteur de base de données pour les tests"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    # Ne pas créer/supprimer les tables en production - elles existent déjà
    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Fournit une session de base de données pour les tests"""
    AsyncTestingSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Fournit un client HTTP pour les tests"""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_store(test_db):
    """Crée un magasin de test"""
    from app.models.store import Store

    store = Store(
        name="Test Store",
        currency="XOF",
        is_active=True
    )
    test_db.add(store)
    await test_db.commit()
    await test_db.refresh(store)

    return store


@pytest.fixture
async def test_user(test_db, test_store):
    """Crée un utilisateur de test"""
    from app.models.user import User
    from app.core.security import get_password_hash

    # Créer un utilisateur de test
    user = User(
        email="test@commercia.com",
        password_hash=get_password_hash("password123"),
        role="admin",
        store_id=test_store.id,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    return user


@pytest.fixture
async def auth_headers(client, test_user):
    """Fournit des headers d'authentification pour les tests"""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
