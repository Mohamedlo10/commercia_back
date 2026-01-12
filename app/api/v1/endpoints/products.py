"""
Endpoints pour la gestion des produits
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.product import Product, ProductVariant
from app.models.category import Category
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithRelations,
    ProductListResponse,
    ProductFilter,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse
)

router = APIRouter(prefix="/products", tags=["Products"])


# ========== HELPER FUNCTIONS ==========

async def get_product_by_id(
    product_id: UUID,
    db: AsyncSession,
    store_id: UUID,
    load_relations: bool = False
) -> Product:
    """Récupère un produit par son ID"""
    query = select(Product).where(
        Product.id == product_id,
        Product.store_id == store_id
    )

    if load_relations:
        query = query.options(
            selectinload(Product.category),
            selectinload(Product.variants)
        )

    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produit non trouvé"
        )

    return product


async def check_sku_uniqueness(
    sku: str,
    store_id: UUID,
    db: AsyncSession,
    exclude_id: Optional[UUID] = None
) -> bool:
    """Vérifie l'unicité du SKU dans le store"""
    query = select(Product).where(
        Product.store_id == store_id,
        Product.sku == sku
    )

    if exclude_id:
        query = query.where(Product.id != exclude_id)

    result = await db.execute(query)
    return result.scalar_one_or_none() is None


def calculate_stock_status(product: Product) -> str:
    """Calcule le statut du stock d'un produit"""
    if not product.track_stock:
        return "not_tracked"

    if product.has_variants:
        total_stock = sum(v.stock_quantity for v in product.variants if v.is_active)
    else:
        total_stock = product.stock_quantity_primary

    if total_stock <= 0:
        return "out_of_stock"
    elif total_stock <= product.stock_alert_threshold:
        return "low_stock"
    else:
        return "in_stock"


# ========== ENDPOINTS CRUD PRODUITS ==========

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Créer un nouveau produit

    - **name**: Nom du produit (obligatoire)
    - **sku**: Code SKU unique (optionnel)
    - **barcode**: Code-barres (optionnel)
    - **category_id**: ID de la catégorie
    - **prix_achat**: Prix d'achat
    - **prix_vente**: Prix de vente
    - **has_multiple_units**: Gestion multi-unités
    - **has_variants**: Le produit a des variantes
    """
    # Vérifier que la catégorie existe
    if product_data.category_id:
        result = await db.execute(
            select(Category).where(
                Category.id == product_data.category_id,
                Category.store_id == product_data.store_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catégorie non trouvée"
            )

    # Vérifier l'unicité du SKU si fourni
    if product_data.sku:
        if not await check_sku_uniqueness(product_data.sku, product_data.store_id, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un produit avec ce SKU existe déjà"
            )

    # Calculer le prix TTC
    prix_ttc = product_data.prix_vente * (1 + product_data.tva_rate / 100)

    # Créer le produit
    new_product = Product(
        **product_data.model_dump(exclude={'prix_vente_ttc'}),
        prix_vente_ttc=prix_ttc
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    # Ajouter les champs calculés
    new_product.is_in_stock = new_product.stock_quantity_primary > 0 or new_product.stock_quantity_secondary > 0
    new_product.stock_status = calculate_stock_status(new_product)

    return new_product


@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de la page"),
    search: Optional[str] = Query(None, description="Recherche dans nom, SKU, code-barres"),
    category_id: Optional[UUID] = Query(None, description="Filtrer par catégorie"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    track_stock: Optional[bool] = Query(None, description="Filtrer produits suivis en stock"),
    has_variants: Optional[bool] = Query(None, description="Filtrer produits avec variantes"),
    in_stock_only: bool = Query(False, description="Uniquement produits en stock"),
    min_price: Optional[float] = Query(None, ge=0, description="Prix minimum"),
    max_price: Optional[float] = Query(None, ge=0, description="Prix maximum"),
    sort_by: str = Query("created_at", description="Tri: name, price, stock, created_at"),
    sort_order: str = Query("desc", description="Ordre: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lister les produits avec pagination et filtres avancés
    """
    # Construction de la requête
    query = select(Product).where(Product.store_id == current_user.store_id)

    # Filtres de recherche
    if search:
        query = query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%"),
                Product.barcode.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )

    # Filtres standards
    if category_id:
        query = query.where(Product.category_id == category_id)

    if is_active is not None:
        query = query.where(Product.is_active == is_active)

    if track_stock is not None:
        query = query.where(Product.track_stock == track_stock)

    if has_variants is not None:
        query = query.where(Product.has_variants == has_variants)

    if in_stock_only:
        query = query.where(
            or_(
                Product.stock_quantity_primary > 0,
                Product.stock_quantity_secondary > 0,
                Product.track_stock == False
            )
        )

    # Filtres de prix
    if min_price is not None:
        query = query.where(Product.prix_vente >= min_price)

    if max_price is not None:
        query = query.where(Product.prix_vente <= max_price)

    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Tri
    sort_column = {
        "name": Product.name,
        "price": Product.prix_vente,
        "stock": Product.stock_quantity_primary,
        "created_at": Product.created_at
    }.get(sort_by, Product.created_at)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Exécution
    result = await db.execute(query)
    products = result.scalars().all()

    # Ajouter les champs calculés
    products_response = []
    for product in products:
        product.is_in_stock = product.stock_quantity_primary > 0 or product.stock_quantity_secondary > 0
        product.stock_status = calculate_stock_status(product)
        products_response.append(product)

    return ProductListResponse(
        items=products_response,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{product_id}", response_model=ProductWithRelations)
async def get_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer un produit par son ID avec ses relations (catégorie, variantes)
    """
    product = await get_product_by_id(
        product_id,
        db,
        current_user.store_id,
        load_relations=True
    )

    # Ajouter les champs calculés
    product.is_in_stock = product.stock_quantity_primary > 0 or product.stock_quantity_secondary > 0
    product.stock_status = calculate_stock_status(product)

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mettre à jour un produit
    """
    product = await get_product_by_id(product_id, db, current_user.store_id)

    # Vérifier l'unicité du SKU si changé
    if product_data.sku and product_data.sku != product.sku:
        if not await check_sku_uniqueness(product_data.sku, current_user.store_id, db, product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un produit avec ce SKU existe déjà"
            )

    # Vérifier que la catégorie existe si changée
    if product_data.category_id and product_data.category_id != product.category_id:
        result = await db.execute(
            select(Category).where(
                Category.id == product_data.category_id,
                Category.store_id == current_user.store_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catégorie non trouvée"
            )

    # Mettre à jour les champs
    update_data = product_data.model_dump(exclude_unset=True)

    # Recalculer le prix TTC si le prix de vente ou la TVA change
    if 'prix_vente' in update_data or 'tva_rate' in update_data:
        prix_vente = update_data.get('prix_vente', product.prix_vente)
        tva_rate = update_data.get('tva_rate', product.tva_rate)
        update_data['prix_vente_ttc'] = prix_vente * (1 + tva_rate / 100)

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    # Ajouter les champs calculés
    product.is_in_stock = product.stock_quantity_primary > 0 or product.stock_quantity_secondary > 0
    product.stock_status = calculate_stock_status(product)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprimer un produit

    Note: Utilisez plutôt is_active=false pour archiver un produit
    """
    product = await get_product_by_id(product_id, db, current_user.store_id)

    # Vérifier qu'il n'y a pas de commandes en cours avec ce produit
    # TODO: Ajouter cette vérification quand le module commandes sera prêt

    # Supprimer les variantes associées
    if product.has_variants:
        await db.execute(
            delete(ProductVariant).where(ProductVariant.product_id == product_id)
        )

    # Supprimer le produit
    await db.delete(product)
    await db.commit()

    return None


# ========== ENDPOINTS VARIANTES ==========

@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(
    product_id: UUID,
    variant_data: ProductVariantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Créer une variante de produit

    Le produit doit avoir has_variants=True
    """
    product = await get_product_by_id(product_id, db, current_user.store_id)

    if not product.has_variants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce produit n'accepte pas de variantes. Définissez has_variants=true d'abord."
        )

    # Vérifier l'unicité du SKU si fourni
    if variant_data.sku:
        result = await db.execute(
            select(ProductVariant).where(
                ProductVariant.sku == variant_data.sku
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une variante avec ce SKU existe déjà"
            )

    # Créer la variante
    new_variant = ProductVariant(
        product_id=product_id,
        **variant_data.model_dump()
    )

    db.add(new_variant)
    await db.commit()
    await db.refresh(new_variant)

    return new_variant


@router.get("/{product_id}/variants", response_model=List[ProductVariantResponse])
async def list_product_variants(
    product_id: UUID,
    include_inactive: bool = Query(False, description="Inclure les variantes inactives"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lister les variantes d'un produit
    """
    product = await get_product_by_id(product_id, db, current_user.store_id)

    query = select(ProductVariant).where(ProductVariant.product_id == product_id)

    if not include_inactive:
        query = query.where(ProductVariant.is_active == True)

    query = query.order_by(ProductVariant.created_at)

    result = await db.execute(query)
    variants = result.scalars().all()

    return variants


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_product_variant(
    product_id: UUID,
    variant_id: UUID,
    variant_data: ProductVariantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mettre à jour une variante de produit
    """
    # Vérifier que le produit existe
    product = await get_product_by_id(product_id, db, current_user.store_id)

    # Récupérer la variante
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id
        )
    )
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variante non trouvée"
        )

    # Vérifier l'unicité du SKU si changé
    if variant_data.sku and variant_data.sku != variant.sku:
        result = await db.execute(
            select(ProductVariant).where(
                ProductVariant.sku == variant_data.sku,
                ProductVariant.id != variant_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une variante avec ce SKU existe déjà"
            )

    # Mettre à jour les champs
    update_data = variant_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)

    await db.commit()
    await db.refresh(variant)

    return variant


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_variant(
    product_id: UUID,
    variant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprimer une variante de produit
    """
    # Vérifier que le produit existe
    product = await get_product_by_id(product_id, db, current_user.store_id)

    # Récupérer la variante
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id
        )
    )
    variant = result.scalar_one_or_none()

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variante non trouvée"
        )

    # Supprimer la variante
    await db.delete(variant)
    await db.commit()

    return None


# ========== ENDPOINTS UTILITAIRES ==========

@router.post("/{product_id}/duplicate", response_model=ProductResponse)
async def duplicate_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Dupliquer un produit (avec variantes)
    """
    product = await get_product_by_id(product_id, db, current_user.store_id, load_relations=True)

    # Créer une copie du produit
    new_product_data = {
        col.name: getattr(product, col.name)
        for col in product.__table__.columns
        if col.name not in ['id', 'created_at', 'updated_at']
    }

    # Modifier le nom et le SKU pour éviter les conflits
    new_product_data['name'] = f"{product.name} (Copie)"
    if product.sku:
        new_product_data['sku'] = f"{product.sku}-COPY"

    # Réinitialiser le stock
    new_product_data['stock_quantity_primary'] = 0
    new_product_data['stock_quantity_secondary'] = 0

    new_product = Product(**new_product_data)
    db.add(new_product)
    await db.flush()

    # Dupliquer les variantes si présentes
    if product.has_variants and product.variants:
        for variant in product.variants:
            variant_data = {
                col.name: getattr(variant, col.name)
                for col in variant.__table__.columns
                if col.name not in ['id', 'product_id', 'created_at', 'updated_at']
            }

            # Modifier le SKU de la variante
            if variant.sku:
                variant_data['sku'] = f"{variant.sku}-COPY"

            # Réinitialiser le stock
            variant_data['stock_quantity'] = 0

            new_variant = ProductVariant(product_id=new_product.id, **variant_data)
            db.add(new_variant)

    await db.commit()
    await db.refresh(new_product)

    # Ajouter les champs calculés
    new_product.is_in_stock = False
    new_product.stock_status = "out_of_stock"

    return new_product


@router.patch("/{product_id}/toggle-active", response_model=ProductResponse)
async def toggle_product_active(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activer/Désactiver un produit
    """
    product = await get_product_by_id(product_id, db, current_user.store_id)

    product.is_active = not product.is_active
    await db.commit()
    await db.refresh(product)

    # Ajouter les champs calculés
    product.is_in_stock = product.stock_quantity_primary > 0 or product.stock_quantity_secondary > 0
    product.stock_status = calculate_stock_status(product)

    return product
