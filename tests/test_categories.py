"""
Tests pour les endpoints de gestion des catégories
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.category import Category
from app.models.store import Store


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de création d'une catégorie"""
    category_data = {
        "name": "Électronique",
        "description": "Produits électroniques",
        "store_id": str(test_store.id),
        "is_active": True,
        "display_order": 1
    }

    response = await client.post(
        "/api/v1/categories/",
        json=category_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Électronique"
    assert data["description"] == "Produits électroniques"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de listage des catégories"""
    # Créer quelques catégories de test
    categories = [
        Category(name="Cat 1", store_id=test_store.id, display_order=1),
        Category(name="Cat 2", store_id=test_store.id, display_order=2),
        Category(name="Cat 3", store_id=test_store.id, display_order=3),
    ]
    for cat in categories:
        test_db.add(cat)
    await test_db.commit()

    response = await client.get(
        "/api/v1/categories/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_get_category_tree(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de récupération de l'arbre des catégories"""
    # Créer une hiérarchie de catégories
    parent = Category(name="Parent", store_id=test_store.id, display_order=1)
    test_db.add(parent)
    await test_db.flush()

    child1 = Category(name="Child 1", store_id=test_store.id, parent_id=parent.id, display_order=1)
    child2 = Category(name="Child 2", store_id=test_store.id, parent_id=parent.id, display_order=2)
    test_db.add(child1)
    test_db.add(child2)
    await test_db.commit()

    response = await client.get(
        "/api/v1/categories/tree",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert data["total_count"] >= 3


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de mise à jour d'une catégorie"""
    # Créer une catégorie
    category = Category(name="Original", store_id=test_store.id, display_order=1)
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    # Mettre à jour
    update_data = {
        "name": "Updated",
        "description": "Updated description"
    }

    response = await client.put(
        f"/api/v1/categories/{category.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de suppression d'une catégorie"""
    # Créer une catégorie
    category = Category(name="To Delete", store_id=test_store.id, display_order=1)
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    response = await client.delete(
        f"/api/v1/categories/{category.id}",
        headers=auth_headers
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_category_duplicate_name(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de création d'une catégorie avec un nom déjà existant"""
    # Créer une catégorie
    category = Category(name="Duplicate", store_id=test_store.id, display_order=1)
    test_db.add(category)
    await test_db.commit()

    # Tenter de créer une autre catégorie avec le même nom
    category_data = {
        "name": "Duplicate",
        "store_id": str(test_store.id),
        "is_active": True
    }

    response = await client.post(
        "/api/v1/categories/",
        json=category_data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "existe déjà" in response.json()["detail"]


@pytest.mark.asyncio
async def test_search_categories(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de recherche de catégories"""
    # Créer des catégories
    categories = [
        Category(name="Électronique", store_id=test_store.id, display_order=1),
        Category(name="Vêtements", store_id=test_store.id, display_order=2),
        Category(name="Alimentation", store_id=test_store.id, display_order=3),
    ]
    for cat in categories:
        test_db.add(cat)
    await test_db.commit()

    response = await client.get(
        "/api/v1/categories/?search=Électronique",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Électronique" in item["name"] for item in data["items"])
