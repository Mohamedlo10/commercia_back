"""
Tests pour l'authentification
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test de connexion réussie"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@commercia.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "test@commercia.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test de connexion avec mauvais mot de passe"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@commercia.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou mot de passe incorrect"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test de connexion avec utilisateur inexistant"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@commercia.com",
            "password": "password123"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """Test de récupération des infos de l'utilisateur connecté"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "test@commercia.com"
    assert data["role"] == "admin"
    assert "id" in data
    assert "store_id" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test d'accès non autorisé"""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 403  # Forbidden without token


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, auth_headers):
    """Test de changement de mot de passe"""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "password123",
            "new_password": "newpassword123"
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Mot de passe modifié avec succès"

    # Vérifier que la connexion fonctionne avec le nouveau mot de passe
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@commercia.com",
            "password": "newpassword123"
        }
    )

    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(client: AsyncClient, auth_headers):
    """Test de changement de mot de passe avec mauvais ancien mot de passe"""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "wrongpassword",
            "new_password": "newpassword123"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Ancien mot de passe incorrect"


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers):
    """Test de déconnexion"""
    response = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Déconnexion réussie"
