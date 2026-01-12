"""
Schémas pour l'authentification
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    """Schéma pour la requête de connexion"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Schéma pour la réponse de connexion"""
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    role: str
    store_id: UUID


class RegisterRequest(BaseModel):
    """Schéma pour l'enregistrement d'un nouvel utilisateur"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="cashier")
    store_id: UUID


class ChangePasswordRequest(BaseModel):
    """Schéma pour changer le mot de passe"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class TokenPayload(BaseModel):
    """Schéma pour le payload du token JWT"""
    sub: UUID
    exp: int
    iat: int
