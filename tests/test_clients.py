"""
Tests pour les endpoints de gestion des clients
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.store import Store


@pytest.mark.asyncio
async def test_create_client(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de création d'un client"""
    client_data = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@example.com",
        "phone": "221771234567",
        "address": "123 Rue de Dakar",
        "city": "Dakar",
        "country": "Sénégal",
        "store_id": str(test_store.id),
        "loyalty_tier": "bronze",
        "credit_limit": 50000
    }

    response = await client.post(
        "/api/v1/clients/",
        json=client_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Jean"
    assert data["last_name"] == "Dupont"
    assert data["email"] == "jean.dupont@example.com"
    assert "client_code" in data
    assert data["loyalty_points"] == 0


@pytest.mark.asyncio
async def test_list_clients(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de listage des clients"""
    # Créer quelques clients
    clients = [
        Client(
            first_name="Client", last_name="1", phone="221771111111",
            store_id=test_store.id, client_code="CLI-001"
        ),
        Client(
            first_name="Client", last_name="2", phone="221772222222",
            store_id=test_store.id, client_code="CLI-002"
        ),
        Client(
            first_name="Client", last_name="3", phone="221773333333",
            store_id=test_store.id, client_code="CLI-003"
        ),
    ]
    for c in clients:
        test_db.add(c)
    await test_db.commit()

    response = await client.get(
        "/api/v1/clients/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_get_client(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de récupération d'un client"""
    test_client = Client(
        first_name="Test",
        last_name="Client",
        phone="221779999999",
        email="test@example.com",
        store_id=test_store.id,
        client_code="CLI-TEST"
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    response = await client.get(
        f"/api/v1/clients/{test_client.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Client"


@pytest.mark.asyncio
async def test_update_client(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de mise à jour d'un client"""
    test_client = Client(
        first_name="Original",
        last_name="Name",
        phone="221778888888",
        store_id=test_store.id,
        client_code="CLI-UPD"
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    update_data = {
        "first_name": "Updated",
        "email": "updated@example.com",
        "loyalty_tier": "silver"
    }

    response = await client.put(
        f"/api/v1/clients/{test_client.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["email"] == "updated@example.com"
    assert data["loyalty_tier"] == "silver"


@pytest.mark.asyncio
async def test_delete_client_without_orders(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de suppression d'un client sans commandes"""
    test_client = Client(
        first_name="To",
        last_name="Delete",
        phone="221777777777",
        store_id=test_store.id,
        client_code="CLI-DEL"
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    response = await client.delete(
        f"/api/v1/clients/{test_client.id}",
        headers=auth_headers
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_client_duplicate_phone(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de création d'un client avec un téléphone déjà existant"""
    # Créer un client
    existing = Client(
        first_name="Existing",
        last_name="Client",
        phone="221776666666",
        store_id=test_store.id,
        client_code="CLI-EX"
    )
    test_db.add(existing)
    await test_db.commit()

    # Tenter de créer un autre client avec le même téléphone
    client_data = {
        "first_name": "Another",
        "last_name": "Client",
        "phone": "221776666666",
        "store_id": str(test_store.id)
    }

    response = await client.post(
        "/api/v1/clients/",
        json=client_data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "téléphone existe déjà" in response.json()["detail"]


@pytest.mark.asyncio
async def test_search_clients(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de recherche rapide de clients"""
    clients = [
        Client(first_name="Alice", last_name="Smith", phone="221771111111", store_id=test_store.id, client_code="CLI-A"),
        Client(first_name="Bob", last_name="Johnson", phone="221772222222", store_id=test_store.id, client_code="CLI-B"),
        Client(first_name="Charlie", last_name="Brown", phone="221773333333", store_id=test_store.id, client_code="CLI-C"),
    ]
    for c in clients:
        test_db.add(c)
    await test_db.commit()

    response = await client.get(
        "/api/v1/clients/search?q=Alice",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("Alice" in c["first_name"] for c in data)


@pytest.mark.asyncio
async def test_adjust_loyalty_points(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test d'ajustement des points de fidélité"""
    test_client = Client(
        first_name="Loyalty",
        last_name="Test",
        phone="221775555555",
        store_id=test_store.id,
        client_code="CLI-LOY",
        loyalty_points=100
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    adjustment_data = {
        "points": 50,
        "reason": "Bonus anniversaire"
    }

    response = await client.post(
        f"/api/v1/clients/{test_client.id}/loyalty/adjust",
        json=adjustment_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["loyalty_points"] == 150


@pytest.mark.asyncio
async def test_redeem_loyalty_points(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test d'utilisation des points de fidélité"""
    test_client = Client(
        first_name="Redeem",
        last_name="Test",
        phone="221774444444",
        store_id=test_store.id,
        client_code="CLI-RED",
        loyalty_points=500
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    response = await client.post(
        f"/api/v1/clients/{test_client.id}/loyalty/redeem?points=100",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["points_to_redeem"] == 100
    assert data["discount_amount"] == 10000  # 100 points * 100 XOF
    assert data["remaining_points"] == 400


@pytest.mark.asyncio
async def test_toggle_client_active(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test d'activation/désactivation d'un client"""
    test_client = Client(
        first_name="Toggle",
        last_name="Test",
        phone="221770000000",
        store_id=test_store.id,
        client_code="CLI-TOG",
        is_active=True
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    response = await client.patch(
        f"/api/v1/clients/{test_client.id}/toggle-active",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False


@pytest.mark.asyncio
async def test_filter_clients_by_loyalty_tier(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de filtrage des clients par niveau de fidélité"""
    clients = [
        Client(first_name="Gold", last_name="Member", phone="221771000000", store_id=test_store.id,
               client_code="CLI-G", loyalty_tier="gold"),
        Client(first_name="Bronze", last_name="Member", phone="221772000000", store_id=test_store.id,
               client_code="CLI-BR", loyalty_tier="bronze"),
    ]
    for c in clients:
        test_db.add(c)
    await test_db.commit()

    response = await client.get(
        "/api/v1/clients/?loyalty_tier=gold",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["loyalty_tier"] == "gold" for item in data["items"])


@pytest.mark.asyncio
async def test_get_client_stats(client: AsyncClient, test_db: AsyncSession, auth_headers: dict, test_store: Store):
    """Test de récupération des statistiques d'un client"""
    test_client = Client(
        first_name="Stats",
        last_name="Test",
        phone="221779000000",
        store_id=test_store.id,
        client_code="CLI-STAT",
        loyalty_points=250,
        total_debt=5000
    )
    test_db.add(test_client)
    await test_db.commit()
    await test_db.refresh(test_client)

    response = await client.get(
        f"/api/v1/clients/{test_client.id}/stats",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == str(test_client.id)
    assert data["loyalty_points"] == 250
    assert data["total_debt"] == 5000
    assert "total_orders" in data
    assert "total_spent" in data
