"""
Tests pour les endpoints de gestion des produits
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.product import Product, ProductVariant
from app.models.category import Category
from app.models.store import Store


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de création d'un produit"""
    # Créer une catégorie
    category = Category(name="Test Cat", store_id=test_store.id)
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)

    product_data = {
        "name": "Laptop HP",
        "description": "Ordinateur portable HP",
        "sku": "LAP-HP-001",
        "barcode": "1234567890123",
        "category_id": str(category.id),
        "store_id": str(test_store.id),
        "prix_achat": 500000,
        "prix_vente": 750000,
        "tva_rate": 18,
        "track_stock": True,
        "has_multiple_units": False,
        "primary_unit": "pièce",
        "stock_alert_threshold": 5
    }

    response = await client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Laptop HP"
    assert data["sku"] == "LAP-HP-001"
    assert data["prix_achat"] == 500000
    assert "id" in data


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de listage des produits"""
    # Créer quelques produits
    products = [
        Product(name="Prod 1", store_id=test_store.id, prix_achat=100, prix_vente=150, tva_rate=0),
        Product(name="Prod 2", store_id=test_store.id, prix_achat=200, prix_vente=300, tva_rate=0),
        Product(name="Prod 3", store_id=test_store.id, prix_achat=300, prix_vente=450, tva_rate=0),
    ]
    for prod in products:
        test_db.add(prod)
    await test_db.commit()

    response = await client.get(
        "/api/v1/products/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de récupération d'un produit"""
    product = Product(
        name="Test Product",
        store_id=test_store.id,
        prix_achat=1000,
        prix_vente=1500,
        tva_rate=18
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)

    response = await client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["prix_achat"] == 1000


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de mise à jour d'un produit"""
    product = Product(
        name="Original",
        store_id=test_store.id,
        prix_achat=1000,
        prix_vente=1500,
        tva_rate=0
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)

    update_data = {
        "name": "Updated Product",
        "prix_vente": 2000
    }

    response = await client.put(
        f"/api/v1/products/{product.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product"


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de suppression d'un produit"""
    product = Product(
        name="To Delete",
        store_id=test_store.id,
        prix_achat=1000,
        prix_vente=1500,
        tva_rate=0
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)

    response = await client.delete(
        f"/api/v1/products/{product.id}",
        headers=auth_headers
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_product_with_variants(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de création d'un produit avec variantes"""
    product = Product(
        name="T-Shirt",
        store_id=test_store.id,
        prix_achat=5000,
        prix_vente=10000,
        tva_rate=18,
        has_variants=True,
        variant_attributes={"couleur": ["Rouge", "Bleu"], "taille": ["S", "M", "L"]}
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)

    # Créer une variante
    variant_data = {
        "name": "T-Shirt Rouge M",
        "sku": "TSH-ROU-M",
        "attributes": {"couleur": "Rouge", "taille": "M"},
        "price": 10000,
        "cost_price": 5000,
        "stock_quantity": 50
    }

    response = await client.post(
        f"/api/v1/products/{product.id}/variants",
        json=variant_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["attributes"]["couleur"] == "Rouge"
    assert data["attributes"]["taille"] == "M"


@pytest.mark.asyncio
async def test_list_product_variants(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de listage des variantes d'un produit"""
    product = Product(
        name="T-Shirt",
        store_id=test_store.id,
        prix_achat=5000,
        prix_vente=10000,
        tva_rate=18,
        has_variants=True
    )
    test_db.add(product)
    await test_db.flush()

    # Créer des variantes
    variants = [
        ProductVariant(
            product_id=product.id,
            name="Rouge M",
            attributes={"couleur": "Rouge", "taille": "M"},
            price=10000,
            stock_quantity=50
        ),
        ProductVariant(
            product_id=product.id,
            name="Bleu L",
            attributes={"couleur": "Bleu", "taille": "L"},
            price=10000,
            stock_quantity=30
        ),
    ]
    for variant in variants:
        test_db.add(variant)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/products/{product.id}/variants",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_duplicate_product(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de duplication d'un produit"""
    product = Product(
        name="Original Product",
        sku="ORIG-001",
        store_id=test_store.id,
        prix_achat=1000,
        prix_vente=1500,
        tva_rate=18,
        stock_quantity_primary=100
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)

    response = await client.post(
        f"/api/v1/products/{product.id}/duplicate",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "(Copie)" in data["name"]
    assert data["stock_quantity_primary"] == 0  # Le stock est réinitialisé


@pytest.mark.asyncio
async def test_toggle_product_active(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test d'activation/désactivation d'un produit"""
    product = Product(
        name="Test Product",
        store_id=test_store.id,
        prix_achat=1000,
        prix_vente=1500,
        tva_rate=0,
        is_active=True
    )
    test_db.add(product)
    await test_db.commit()
    await test_db.refresh(product)

    response = await client.patch(
        f"/api/v1/products/{product.id}/toggle-active",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de recherche de produits"""
    products = [
        Product(name="Laptop HP", sku="LAP-HP", store_id=test_store.id, prix_achat=500000, prix_vente=750000, tva_rate=0),
        Product(name="Mouse Logitech", sku="MOU-LOG", store_id=test_store.id, prix_achat=15000, prix_vente=25000, tva_rate=0),
        Product(name="Keyboard Corsair", sku="KEY-COR", store_id=test_store.id, prix_achat=50000, prix_vente=75000, tva_rate=0),
    ]
    for prod in products:
        test_db.add(prod)
    await test_db.commit()

    response = await client.get(
        "/api/v1/products/?search=Laptop",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Laptop" in item["name"] for item in data["items"])


@pytest.mark.asyncio
async def test_filter_products_by_category(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de filtrage des produits par catégorie"""
    category = Category(name="Electronics", store_id=test_store.id)
    test_db.add(category)
    await test_db.flush()

    product = Product(
        name="Laptop",
        category_id=category.id,
        store_id=test_store.id,
        prix_achat=500000,
        prix_vente=750000,
        tva_rate=0
    )
    test_db.add(product)
    await test_db.commit()

    response = await client.get(
        f"/api/v1/products/?category_id={category.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
