"""
Configuration pytest
Fixtures partagées pour les tests
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# URL de la base de données de test (différente de la production)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/commercia_test"


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

    # Créer toutes les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Supprimer toutes les tables après les tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

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
async def test_user(test_db):
    """Crée un utilisateur de test"""
    from app.models.user import User
    from app.models.store import Store
    from app.core.security import get_password_hash

    # Créer un magasin de test
    store = Store(
        name="Test Store",
        currency="XOF",
        is_active=True
    )
    test_db.add(store)
    await test_db.commit()
    await test_db.refresh(store)

    # Créer un utilisateur de test
    user = User(
        email="test@commercia.com",
        password_hash=get_password_hash("password123"),
        role="admin",
        store_id=store.id,
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
