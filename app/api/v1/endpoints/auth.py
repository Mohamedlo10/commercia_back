"""
Endpoints d'authentification
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, ChangePasswordRequest

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Connexion d'un utilisateur

    - **email**: Email de l'utilisateur
    - **password**: Mot de passe

    Retourne un token JWT d'accès
    """
    # Récupérer l'utilisateur par email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    # Vérifier si l'utilisateur existe et si le mot de passe est correct
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Vérifier si l'utilisateur est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé"
        )

    # Mettre à jour la date de dernière connexion
    user.last_login = datetime.utcnow()
    await db.commit()

    # Créer le token d'accès
    access_token = create_access_token(subject=str(user.id))

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role,
        store_id=user.store_id
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Enregistrement d'un nouvel utilisateur

    - **email**: Email de l'utilisateur
    - **password**: Mot de passe
    - **role**: Rôle de l'utilisateur (admin, manager, cashier, seller)
    - **store_id**: ID du magasin

    Note: Dans un environnement de production, cette route devrait être protégée
    et réservée aux administrateurs.
    """
    # Vérifier si l'email existe déjà
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )

    # Créer le nouvel utilisateur
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        store_id=user_data.store_id,
        is_active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Créer le token d'accès
    access_token = create_access_token(subject=str(new_user.id))

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role,
        store_id=new_user.store_id
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les informations de l'utilisateur actuellement connecté
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "store_id": current_user.store_id,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login,
        "created_at": current_user.created_at
    }


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change le mot de passe de l'utilisateur actuel

    - **old_password**: Ancien mot de passe
    - **new_password**: Nouveau mot de passe
    """
    # Vérifier l'ancien mot de passe
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ancien mot de passe incorrect"
        )

    # Mettre à jour le mot de passe
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "Mot de passe modifié avec succès"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Déconnexion de l'utilisateur

    Note: Avec JWT, la déconnexion côté serveur est limitée.
    Le client doit simplement supprimer le token.
    Cette route sert principalement à confirmer la déconnexion.
    """
    return {"message": "Déconnexion réussie"}
