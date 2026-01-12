"""
Utilitaires de sécurité
Gestion JWT, hashing des mots de passe, authentification
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


# Configuration du hashing de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration du bearer token
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash un mot de passe"""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT

    Args:
        subject: L'identifiant de l'utilisateur (généralement user_id)
        expires_delta: Durée de validité du token

    Returns:
        Token JWT encodé
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Décode un token JWT

    Args:
        token: Token JWT à décoder

    Returns:
        Payload du token ou None si invalide
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dépendance FastAPI pour récupérer l'utilisateur authentifié

    Usage:
        @app.get("/me")
        async def read_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extraire le token
    token = credentials.credentials

    # Décoder le token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Récupérer l'utilisateur depuis la DB
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur inactif"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dépendance pour s'assurer que l'utilisateur est actif
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur inactif"
        )
    return current_user


def check_user_permission(user: User, resource: str, action: str) -> bool:
    """
    Vérifie si un utilisateur a la permission d'effectuer une action

    Args:
        user: L'utilisateur
        resource: La ressource (ex: "products", "orders")
        action: L'action (ex: "read", "create", "update", "delete")

    Returns:
        True si l'utilisateur a la permission
    """
    # Les admins ont tous les droits
    if user.role == "admin":
        return True

    # TODO: Implémenter la logique de vérification des permissions
    # depuis la table permissions en fonction du rôle
    return False


class PermissionChecker:
    """
    Classe pour créer des dépendances de vérification de permissions

    Usage:
        require_product_create = PermissionChecker("products", "create")

        @app.post("/products")
        async def create_product(
            user: User = Depends(require_product_create)
        ):
            ...
    """

    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not check_user_permission(user, self.resource, self.action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission refusée: {self.action} sur {self.resource}"
            )
        return user
