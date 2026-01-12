"""
Endpoints pour la gestion des clients
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.client import Client
from app.models.order import Order
from app.models.transaction import Transaction
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientWithStats,
    ClientListResponse,
    ClientStats,
    LoyaltyPointsAdjustment,
    DebtPayment
)

router = APIRouter(prefix="/clients", tags=["Clients"])


# ========== HELPER FUNCTIONS ==========

async def get_client_by_id(client_id: UUID, db: AsyncSession, store_id: UUID) -> Client:
    """Récupère un client par son ID"""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.store_id == store_id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )

    return client


async def check_phone_uniqueness(
    phone: str,
    store_id: UUID,
    db: AsyncSession,
    exclude_id: Optional[UUID] = None
) -> bool:
    """Vérifie l'unicité du téléphone dans le store"""
    query = select(Client).where(
        Client.store_id == store_id,
        Client.phone == phone
    )

    if exclude_id:
        query = query.where(Client.id != exclude_id)

    result = await db.execute(query)
    return result.scalar_one_or_none() is None


async def get_client_stats(client_id: UUID, db: AsyncSession) -> dict:
    """Calcule les statistiques d'un client"""
    # Nombre total de commandes
    result = await db.execute(
        select(func.count(Order.id))
        .where(Order.client_id == client_id)
    )
    total_orders = result.scalar() or 0

    # Montant total dépensé
    result = await db.execute(
        select(func.sum(Order.total_amount))
        .where(
            Order.client_id == client_id,
            Order.statut_paiement.in_(['Payer', 'Partiellement'])
        )
    )
    total_spent = result.scalar() or 0.0

    # Panier moyen
    average_order_value = total_spent / total_orders if total_orders > 0 else 0.0

    # Date du dernier achat
    result = await db.execute(
        select(Order.created_at)
        .where(Order.client_id == client_id)
        .order_by(desc(Order.created_at))
        .limit(1)
    )
    last_purchase = result.scalar_one_or_none()

    return {
        'total_orders': total_orders,
        'total_spent': float(total_spent),
        'average_order_value': float(average_order_value),
        'last_purchase_date': last_purchase
    }


# ========== ENDPOINTS CRUD ==========

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Créer un nouveau client

    - **first_name**: Prénom (obligatoire)
    - **last_name**: Nom (obligatoire)
    - **phone**: Téléphone (obligatoire, unique)
    - **email**: Email (optionnel)
    - **address**: Adresse (optionnel)
    - **loyalty_tier**: Niveau de fidélité (bronze par défaut)
    - **credit_limit**: Limite de crédit autorisée
    """
    # Vérifier l'unicité du téléphone
    if not await check_phone_uniqueness(client_data.phone, client_data.store_id, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un client avec ce numéro de téléphone existe déjà"
        )

    # Vérifier l'unicité de l'email si fourni
    if client_data.email:
        result = await db.execute(
            select(Client).where(
                Client.store_id == client_data.store_id,
                Client.email == client_data.email
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un client avec cet email existe déjà"
            )

    # Créer le client (le code client sera généré par le trigger)
    new_client = Client(**client_data.model_dump())
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)

    return new_client


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de la page"),
    search: Optional[str] = Query(None, description="Recherche dans nom, prénom, email, téléphone, code"),
    loyalty_tier: Optional[str] = Query(None, description="Filtrer par niveau de fidélité"),
    has_debt: Optional[bool] = Query(None, description="Filtrer clients avec dette"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    city: Optional[str] = Query(None, description="Filtrer par ville"),
    min_loyalty_points: Optional[int] = Query(None, ge=0, description="Points minimum"),
    sort_by: str = Query("created_at", description="Tri: name, points, debt, last_purchase, created_at"),
    sort_order: str = Query("desc", description="Ordre: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lister les clients avec pagination et filtres
    """
    # Construction de la requête
    query = select(Client).where(Client.store_id == current_user.store_id)

    # Filtres de recherche
    if search:
        query = query.where(
            or_(
                Client.first_name.ilike(f"%{search}%"),
                Client.last_name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%"),
                Client.client_code.ilike(f"%{search}%")
            )
        )

    # Filtres standards
    if loyalty_tier:
        query = query.where(Client.loyalty_tier == loyalty_tier.lower())

    if has_debt is not None:
        if has_debt:
            query = query.where(Client.total_debt > 0)
        else:
            query = query.where(Client.total_debt == 0)

    if is_active is not None:
        query = query.where(Client.is_active == is_active)

    if city:
        query = query.where(Client.city.ilike(f"%{city}%"))

    if min_loyalty_points is not None:
        query = query.where(Client.loyalty_points >= min_loyalty_points)

    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Tri
    sort_column = {
        "name": Client.last_name,
        "points": Client.loyalty_points,
        "debt": Client.total_debt,
        "last_purchase": Client.last_purchase_date,
        "created_at": Client.created_at
    }.get(sort_by, Client.created_at)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Exécution
    result = await db.execute(query)
    clients = result.scalars().all()

    return ClientListResponse(
        items=clients,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/search", response_model=List[ClientResponse])
async def search_clients_quick(
    q: str = Query(..., min_length=2, description="Terme de recherche (min 2 caractères)"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats maximum"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recherche rapide de clients (pour autocomplete)

    Cherche dans: nom, prénom, téléphone, code client
    """
    query = select(Client).where(
        Client.store_id == current_user.store_id,
        or_(
            Client.first_name.ilike(f"%{q}%"),
            Client.last_name.ilike(f"%{q}%"),
            Client.phone.ilike(f"%{q}%"),
            Client.client_code.ilike(f"%{q}%")
        )
    ).limit(limit)

    result = await db.execute(query)
    clients = result.scalars().all()

    return clients


@router.get("/{client_id}", response_model=ClientWithStats)
async def get_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer un client par son ID avec ses statistiques
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Récupérer les statistiques
    stats = await get_client_stats(client_id, db)

    # Construire la réponse avec stats
    client_dict = client.__dict__.copy()
    client_dict.update(stats)
    client_dict['can_purchase_on_credit'] = client.can_purchase_on_credit

    return ClientWithStats(**client_dict)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mettre à jour un client
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Vérifier l'unicité du téléphone si changé
    if client_data.phone and client_data.phone != client.phone:
        if not await check_phone_uniqueness(client_data.phone, current_user.store_id, db, client_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un client avec ce numéro de téléphone existe déjà"
            )

    # Vérifier l'unicité de l'email si changé
    if client_data.email and client_data.email != client.email:
        result = await db.execute(
            select(Client).where(
                Client.store_id == current_user.store_id,
                Client.email == client_data.email,
                Client.id != client_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un client avec cet email existe déjà"
            )

    # Mettre à jour les champs
    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprimer un client

    Note: Impossible de supprimer un client avec des commandes.
    Utilisez plutôt is_active=false pour désactiver le client.
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Vérifier qu'il n'y a pas de commandes
    result = await db.execute(
        select(func.count(Order.id))
        .where(Order.client_id == client_id)
    )
    order_count = result.scalar()

    if order_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer ce client car il a {order_count} commande(s). Désactivez-le plutôt."
        )

    # Supprimer le client
    await db.delete(client)
    await db.commit()

    return None


# ========== ENDPOINTS FIDÉLITÉ ==========

@router.post("/{client_id}/loyalty/adjust", response_model=ClientResponse)
async def adjust_loyalty_points(
    client_id: UUID,
    adjustment: LoyaltyPointsAdjustment,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ajuster manuellement les points de fidélité d'un client

    - **points**: Nombre de points (positif pour ajouter, négatif pour retirer)
    - **reason**: Raison de l'ajustement
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Vérifier qu'on ne passe pas en négatif
    new_points = client.loyalty_points + adjustment.points
    if new_points < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de retirer {abs(adjustment.points)} points. Le client n'a que {client.loyalty_points} points."
        )

    # Ajuster les points
    client.loyalty_points = new_points

    # TODO: Logger l'ajustement dans audit_logs
    # await log_audit(
    #     db=db,
    #     user_id=current_user.id,
    #     action="loyalty_adjustment",
    #     entity_type="client",
    #     entity_id=client_id,
    #     details={
    #         "points": adjustment.points,
    #         "reason": adjustment.reason,
    #         "new_balance": new_points
    #     }
    # )

    await db.commit()
    await db.refresh(client)

    return client


@router.post("/{client_id}/loyalty/redeem", response_model=dict)
async def redeem_loyalty_points(
    client_id: UUID,
    points: int = Query(..., gt=0, description="Nombre de points à utiliser"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Utiliser les points de fidélité pour obtenir une réduction

    1 point = 100 XOF de réduction (configurable)
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Vérifier que le client a assez de points
    if client.loyalty_points < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le client n'a que {client.loyalty_points} points disponibles"
        )

    # Calculer la réduction (1 point = 100 XOF par défaut)
    from app.core.config import settings
    discount_amount = points * settings.LOYALTY_POINTS_VALUE

    return {
        "points_to_redeem": points,
        "discount_amount": discount_amount,
        "remaining_points": client.loyalty_points - points,
        "message": f"{points} points convertis en {discount_amount} XOF de réduction"
    }


# ========== ENDPOINTS DETTE ==========

@router.post("/{client_id}/debt/pay", response_model=ClientResponse)
async def pay_client_debt(
    client_id: UUID,
    payment: DebtPayment,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enregistrer un paiement de dette

    - **amount**: Montant du paiement
    - **payment_method**: Méthode de paiement (Espèces, Mobile Money, etc.)
    - **notes**: Notes optionnelles
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Vérifier que le client a une dette
    if client.total_debt <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce client n'a pas de dette"
        )

    # Vérifier que le montant ne dépasse pas la dette
    if payment.amount > client.total_debt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le montant du paiement ({payment.amount}) dépasse la dette ({client.total_debt})"
        )

    # Créer une transaction de paiement de dette
    # Note: Cette transaction sera liée à une commande existante
    # Pour l'instant on met à jour juste la dette du client
    # Le trigger de la DB se chargera de mettre à jour les montants

    # TODO: Créer la transaction de paiement
    # transaction = Transaction(
    #     store_id=current_user.store_id,
    #     order_id=...,  # Il faudra trouver la commande correspondante
    #     transaction_type="debt_payment",
    #     payment_method=payment.payment_method,
    #     amount=payment.amount,
    #     status="completed"
    # )
    # db.add(transaction)

    # Pour l'instant, mise à jour manuelle
    client.total_debt -= payment.amount

    await db.commit()
    await db.refresh(client)

    return client


@router.get("/{client_id}/stats", response_model=ClientStats)
async def get_client_statistics(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer les statistiques détaillées d'un client
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    # Statistiques globales
    stats = await get_client_stats(client_id, db)

    # Statistiques du mois en cours
    from datetime import datetime
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Commandes ce mois-ci
    result = await db.execute(
        select(func.count(Order.id))
        .where(
            Order.client_id == client_id,
            Order.created_at >= start_of_month
        )
    )
    orders_this_month = result.scalar() or 0

    # Montant dépensé ce mois-ci
    result = await db.execute(
        select(func.sum(Order.total_amount))
        .where(
            Order.client_id == client_id,
            Order.created_at >= start_of_month,
            Order.statut_paiement.in_(['Payer', 'Partiellement'])
        )
    )
    spent_this_month = result.scalar() or 0.0

    return ClientStats(
        client_id=client.id,
        client_name=f"{client.first_name} {client.last_name}",
        total_orders=stats['total_orders'],
        total_spent=stats['total_spent'],
        total_debt=float(client.total_debt),
        loyalty_points=client.loyalty_points,
        loyalty_tier=client.loyalty_tier,
        average_order_value=stats['average_order_value'],
        last_purchase_date=stats['last_purchase_date'],
        orders_this_month=orders_this_month,
        spent_this_month=float(spent_this_month)
    )


# ========== ENDPOINTS UTILITAIRES ==========

@router.patch("/{client_id}/toggle-active", response_model=ClientResponse)
async def toggle_client_active(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activer/Désactiver un client
    """
    client = await get_client_by_id(client_id, db, current_user.store_id)

    client.is_active = not client.is_active
    await db.commit()
    await db.refresh(client)

    return client
