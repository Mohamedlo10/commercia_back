"""
Endpoints pour la gestion du stock
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.product import Product, ProductVariant
from app.models.stock import StockMovement
from app.models.category import Category
from app.schemas.stock import (
    StockMovementCreate,
    StockMovementResponse,
    StockMovementWithProduct,
    StockMovementListResponse,
    StockAdjustment,
    ProductStockInfo,
    VariantStockInfo,
    LowStockAlert,
    StockSummary,
    InventoryCreate,
    InventoryResult,
    MovementType
)

router = APIRouter(prefix="/stock", tags=["Stock Management"])


# ========== HELPER FUNCTIONS ==========

async def get_product_with_stock(
    product_id: UUID,
    db: AsyncSession,
    store_id: UUID
) -> Product:
    """Récupère un produit avec vérification du store"""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.store_id == store_id
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )

    if not product.track_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce produit n'est pas suivi en stock"
        )

    return product


async def create_stock_movement(
    db: AsyncSession,
    store_id: UUID,
    product_id: UUID,
    movement_type: MovementType,
    quantity: float,
    unit: str,
    user_id: UUID,
    variant_id: Optional[UUID] = None,
    order_id: Optional[UUID] = None,
    reference: Optional[str] = None,
    notes: Optional[str] = None
) -> StockMovement:
    """Crée un mouvement de stock et met à jour les quantités"""

    # Récupérer le stock actuel
    if variant_id:
        result = await db.execute(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise HTTPException(status_code=404, detail="Variante non trouvée")
        stock_before = variant.stock_quantity
    else:
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        # Déterminer quelle quantité utiliser selon l'unité
        if unit == product.primary_unit:
            stock_before = product.stock_quantity_primary
        elif unit == product.secondary_unit:
            stock_before = product.stock_quantity_secondary
        else:
            stock_before = product.stock_quantity_primary

    # Calculer le nouveau stock selon le type de mouvement
    if movement_type in [MovementType.PURCHASE, MovementType.RETURN,
                         MovementType.ADJUSTMENT_IN, MovementType.TRANSFER_IN]:
        # Mouvements entrants : augmentent le stock
        stock_after = stock_before + quantity
    else:
        # Mouvements sortants : diminuent le stock
        stock_after = stock_before - quantity
        if stock_after < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuffisant. Stock actuel: {stock_before}, demandé: {quantity}"
            )

    # Créer le mouvement
    movement = StockMovement(
        store_id=store_id,
        product_id=product_id,
        variant_id=variant_id,
        order_id=order_id,
        movement_type=movement_type.value,
        quantity=quantity,
        unit=unit,
        stock_before=stock_before,
        stock_after=stock_after,
        reference=reference,
        notes=notes,
        user_id=user_id
    )

    db.add(movement)

    # Mettre à jour le stock du produit/variante
    if variant_id:
        variant.stock_quantity = stock_after
    else:
        if unit == product.primary_unit:
            product.stock_quantity_primary = stock_after
        elif unit == product.secondary_unit:
            product.stock_quantity_secondary = stock_after
        else:
            product.stock_quantity_primary = stock_after

    await db.flush()
    return movement


# ========== ENDPOINTS MOUVEMENTS DE STOCK ==========

@router.post("/movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_stock_movement(
    movement_data: StockMovementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Créer un mouvement de stock manuel

    Types de mouvements:
    - **purchase**: Achat/Approvisionnement
    - **adjustment_in**: Ajustement positif
    - **adjustment_out**: Ajustement négatif (casse, vol)
    - **transfer_in**: Transfert entrant
    - **transfer_out**: Transfert sortant
    """
    # Vérifier que le produit existe et est suivi en stock
    product = await get_product_with_stock(
        movement_data.product_id,
        db,
        movement_data.store_id
    )

    # Créer le mouvement
    movement = await create_stock_movement(
        db=db,
        store_id=movement_data.store_id,
        product_id=movement_data.product_id,
        movement_type=movement_data.movement_type,
        quantity=movement_data.quantity,
        unit=movement_data.unit,
        user_id=current_user.id,
        variant_id=movement_data.variant_id,
        order_id=movement_data.order_id,
        reference=movement_data.reference,
        notes=movement_data.notes
    )

    await db.commit()
    await db.refresh(movement)

    return movement


@router.get("/movements", response_model=StockMovementListResponse)
async def list_stock_movements(
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de la page"),
    product_id: Optional[UUID] = Query(None, description="Filtrer par produit"),
    movement_type: Optional[MovementType] = Query(None, description="Filtrer par type"),
    date_from: Optional[datetime] = Query(None, description="Date de début"),
    date_to: Optional[datetime] = Query(None, description="Date de fin"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lister les mouvements de stock avec pagination et filtres
    """
    # Construction de la requête
    query = select(StockMovement).where(StockMovement.store_id == current_user.store_id)

    # Filtres
    if product_id:
        query = query.where(StockMovement.product_id == product_id)

    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type.value)

    if date_from:
        query = query.where(StockMovement.created_at >= date_from)

    if date_to:
        query = query.where(StockMovement.created_at <= date_to)

    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Tri et pagination
    query = query.order_by(desc(StockMovement.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Exécution
    result = await db.execute(query)
    movements = result.scalars().all()

    return StockMovementListResponse(
        items=movements,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/movements/{product_id}/history", response_model=List[StockMovementWithProduct])
async def get_product_stock_history(
    product_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Nombre de mouvements"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer l'historique des mouvements de stock d'un produit
    """
    # Vérifier que le produit existe
    product = await get_product_with_stock(product_id, db, current_user.store_id)

    # Récupérer les mouvements
    query = (
        select(StockMovement)
        .where(StockMovement.product_id == product_id)
        .order_by(desc(StockMovement.created_at))
        .limit(limit)
    )

    result = await db.execute(query)
    movements = result.scalars().all()

    # Enrichir avec les informations produit
    movements_with_product = []
    for movement in movements:
        movement_dict = movement.__dict__.copy()
        movement_dict['product_name'] = product.name
        movement_dict['product_sku'] = product.sku

        # Ajouter le nom de la variante si applicable
        if movement.variant_id:
            variant_result = await db.execute(
                select(ProductVariant).where(ProductVariant.id == movement.variant_id)
            )
            variant = variant_result.scalar_one_or_none()
            if variant:
                movement_dict['variant_name'] = str(variant.attributes)

        movements_with_product.append(StockMovementWithProduct(**movement_dict))

    return movements_with_product


# ========== ENDPOINTS AJUSTEMENT DE STOCK ==========

@router.post("/adjust", response_model=StockMovementResponse)
async def adjust_stock(
    adjustment: StockAdjustment,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ajuster le stock d'un produit (inventaire, correction d'erreur)

    Crée automatiquement un mouvement d'ajustement (positif ou négatif)
    """
    # Vérifier que le produit existe
    product = await get_product_with_stock(
        adjustment.product_id,
        db,
        current_user.store_id
    )

    # Récupérer le stock actuel
    if adjustment.variant_id:
        result = await db.execute(
            select(ProductVariant).where(ProductVariant.id == adjustment.variant_id)
        )
        variant = result.scalar_one_or_none()
        if not variant:
            raise HTTPException(status_code=404, detail="Variante non trouvée")
        current_stock = variant.stock_quantity
    else:
        if adjustment.unit == product.primary_unit:
            current_stock = product.stock_quantity_primary
        else:
            current_stock = product.stock_quantity_secondary

    # Calculer la différence
    difference = adjustment.new_quantity - current_stock

    if difference == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nouvelle quantité est identique à la quantité actuelle"
        )

    # Déterminer le type d'ajustement
    movement_type = MovementType.ADJUSTMENT_IN if difference > 0 else MovementType.ADJUSTMENT_OUT

    # Créer le mouvement
    movement = await create_stock_movement(
        db=db,
        store_id=current_user.store_id,
        product_id=adjustment.product_id,
        movement_type=movement_type,
        quantity=abs(difference),
        unit=adjustment.unit,
        user_id=current_user.id,
        variant_id=adjustment.variant_id,
        reference="ADJUSTMENT",
        notes=adjustment.reason
    )

    await db.commit()
    await db.refresh(movement)

    return movement


# ========== ENDPOINTS ÉTAT DU STOCK ==========

@router.get("/current", response_model=List[ProductStockInfo])
async def get_current_stock(
    category_id: Optional[UUID] = Query(None, description="Filtrer par catégorie"),
    in_stock_only: bool = Query(False, description="Uniquement produits en stock"),
    low_stock_only: bool = Query(False, description="Uniquement produits en stock faible"),
    sort_by: str = Query("name", description="Tri: name, stock, value"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer l'état actuel du stock de tous les produits
    """
    # Construction de la requête
    query = (
        select(Product)
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True
        )
        .options(selectinload(Product.category))
    )

    # Filtres
    if category_id:
        query = query.where(Product.category_id == category_id)

    if in_stock_only:
        query = query.where(
            or_(
                Product.stock_quantity_primary > 0,
                Product.stock_quantity_secondary > 0
            )
        )

    if low_stock_only:
        query = query.where(
            Product.stock_quantity_primary <= Product.stock_alert_threshold
        )

    # Tri
    if sort_by == "stock":
        query = query.order_by(Product.stock_quantity_primary)
    elif sort_by == "value":
        query = query.order_by(desc(Product.stock_quantity_primary * Product.prix_achat))
    else:
        query = query.order_by(Product.name)

    result = await db.execute(query)
    products = result.scalars().all()

    # Construire la réponse
    stock_info_list = []
    for product in products:
        # Récupérer le dernier mouvement
        last_movement_result = await db.execute(
            select(StockMovement.created_at)
            .where(StockMovement.product_id == product.id)
            .order_by(desc(StockMovement.created_at))
            .limit(1)
        )
        last_movement_date = last_movement_result.scalar_one_or_none()

        # Calculer le statut du stock
        if product.stock_quantity_primary <= 0:
            stock_status = "out_of_stock"
        elif product.stock_quantity_primary <= product.stock_alert_threshold:
            stock_status = "low_stock"
        else:
            stock_status = "in_stock"

        stock_info = ProductStockInfo(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            category_name=product.category.name if product.category else None,
            stock_quantity_primary=float(product.stock_quantity_primary),
            primary_unit=product.primary_unit,
            stock_quantity_secondary=float(product.stock_quantity_secondary),
            secondary_unit=product.secondary_unit,
            stock_alert_threshold=float(product.stock_alert_threshold),
            is_below_threshold=product.stock_quantity_primary <= product.stock_alert_threshold,
            stock_status=stock_status,
            cost_price=float(product.prix_achat),
            total_stock_value=float(product.stock_quantity_primary * product.prix_achat),
            last_movement_date=last_movement_date,
            has_variants=product.has_variants,
            track_stock=product.track_stock
        )
        stock_info_list.append(stock_info)

    return stock_info_list


@router.get("/low-stock", response_model=List[LowStockAlert])
async def get_low_stock_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer les alertes de stock faible

    Retourne tous les produits et variantes dont le stock est en dessous du seuil d'alerte
    """
    alerts = []

    # Produits sans variantes
    query = (
        select(Product)
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True,
            Product.has_variants == False,
            Product.stock_quantity_primary <= Product.stock_alert_threshold
        )
        .order_by(Product.stock_quantity_primary)
    )

    result = await db.execute(query)
    products = result.scalars().all()

    for product in products:
        alerts.append(LowStockAlert(
            product_id=product.id,
            variant_id=None,
            product_name=product.name,
            variant_name=None,
            current_stock=float(product.stock_quantity_primary),
            alert_threshold=float(product.stock_alert_threshold),
            shortage=float(product.stock_alert_threshold - product.stock_quantity_primary),
            unit=product.primary_unit
        ))

    # Variantes de produits
    query = (
        select(ProductVariant, Product)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True,
            ProductVariant.stock_quantity <= ProductVariant.stock_alert_threshold
        )
        .order_by(ProductVariant.stock_quantity)
    )

    result = await db.execute(query)
    variants_with_products = result.all()

    for variant, product in variants_with_products:
        alerts.append(LowStockAlert(
            product_id=product.id,
            variant_id=variant.id,
            product_name=product.name,
            variant_name=str(variant.attributes),
            current_stock=float(variant.stock_quantity),
            alert_threshold=float(variant.stock_alert_threshold),
            shortage=float(variant.stock_alert_threshold - variant.stock_quantity),
            unit=product.primary_unit
        ))

    return alerts


@router.get("/summary", response_model=StockSummary)
async def get_stock_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer un résumé global du stock
    """
    # Total de produits suivis en stock
    result = await db.execute(
        select(func.count(Product.id))
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True
        )
    )
    total_products = result.scalar() or 0

    # Produits en stock
    result = await db.execute(
        select(func.count(Product.id))
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True,
            Product.stock_quantity_primary > 0
        )
    )
    products_in_stock = result.scalar() or 0

    # Produits en stock faible
    result = await db.execute(
        select(func.count(Product.id))
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True,
            Product.stock_quantity_primary > 0,
            Product.stock_quantity_primary <= Product.stock_alert_threshold
        )
    )
    products_low_stock = result.scalar() or 0

    # Produits en rupture
    result = await db.execute(
        select(func.count(Product.id))
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True,
            Product.stock_quantity_primary <= 0
        )
    )
    products_out_of_stock = result.scalar() or 0

    # Valeur totale du stock
    result = await db.execute(
        select(func.sum(Product.stock_quantity_primary * Product.prix_achat))
        .where(
            Product.store_id == current_user.store_id,
            Product.track_stock == True
        )
    )
    total_stock_value = result.scalar() or 0.0

    # Produits avec variantes
    result = await db.execute(
        select(func.count(Product.id))
        .where(
            Product.store_id == current_user.store_id,
            Product.has_variants == True
        )
    )
    products_with_variants = result.scalar() or 0

    return StockSummary(
        total_products=total_products,
        products_in_stock=products_in_stock,
        products_low_stock=products_low_stock,
        products_out_of_stock=products_out_of_stock,
        total_stock_value=float(total_stock_value),
        products_with_variants=products_with_variants
    )
