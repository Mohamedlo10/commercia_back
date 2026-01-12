"""
Endpoints pour la gestion des catégories de produits
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithChildren,
    CategoryListResponse,
    CategoryTreeResponse,
    CategoryStats
)

router = APIRouter(prefix="/categories", tags=["Categories"])


# ========== HELPER FUNCTIONS ==========

async def get_category_by_id(category_id: UUID, db: AsyncSession, store_id: UUID) -> Category:
    """Récupère une catégorie par son ID"""
    result = await db.execute(
        select(Category)
        .where(Category.id == category_id, Category.store_id == store_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    return category


async def build_category_tree(categories: List[Category]) -> List[dict]:
    """Construit un arbre hiérarchique de catégories"""
    category_dict = {cat.id: cat for cat in categories}
    tree = []

    for category in categories:
        if category.parent_id is None:
            # C'est une catégorie racine
            tree.append(category)
        else:
            # Ajouter comme enfant de la catégorie parente
            parent = category_dict.get(category.parent_id)
            if parent:
                if not hasattr(parent, 'children_list'):
                    parent.children_list = []
                parent.children_list.append(category)

    return tree


async def get_category_product_count(category_id: UUID, db: AsyncSession) -> int:
    """Compte le nombre de produits dans une catégorie"""
    result = await db.execute(
        select(func.count(Product.id))
        .where(Product.category_id == category_id)
    )
    return result.scalar() or 0


# ========== ENDPOINTS CRUD ==========

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Créer une nouvelle catégorie

    - **name**: Nom de la catégorie (obligatoire)
    - **parent_id**: ID de la catégorie parente (optionnel, pour hiérarchie)
    - **description**: Description de la catégorie
    - **image_url**: URL de l'image
    - **display_order**: Ordre d'affichage
    """
    # Vérifier que la catégorie parente existe si spécifiée
    if category_data.parent_id:
        await get_category_by_id(category_data.parent_id, db, category_data.store_id)

    # Vérifier l'unicité du nom dans le store
    result = await db.execute(
        select(Category)
        .where(
            Category.store_id == category_data.store_id,
            Category.name == category_data.name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une catégorie avec ce nom existe déjà"
        )

    # Créer la catégorie
    new_category = Category(**category_data.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)

    return new_category


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de la page"),
    search: Optional[str] = Query(None, description="Recherche dans le nom"),
    parent_id: Optional[UUID] = Query(None, description="Filtrer par catégorie parente"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lister les catégories avec pagination et filtres
    """
    # Construction de la requête
    query = select(Category).where(Category.store_id == current_user.store_id)

    # Filtres
    if search:
        query = query.where(
            or_(
                Category.name.ilike(f"%{search}%"),
                Category.description.ilike(f"%{search}%")
            )
        )

    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)

    if is_active is not None:
        query = query.where(Category.is_active == is_active)

    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Pagination
    query = query.order_by(Category.display_order, Category.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Exécution
    result = await db.execute(query)
    categories = result.scalars().all()

    return CategoryListResponse(
        items=categories,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/tree", response_model=CategoryTreeResponse)
async def get_category_tree(
    include_inactive: bool = Query(False, description="Inclure les catégories inactives"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer l'arbre hiérarchique complet des catégories
    """
    query = select(Category).where(Category.store_id == current_user.store_id)

    if not include_inactive:
        query = query.where(Category.is_active == True)

    query = query.order_by(Category.display_order, Category.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    # Construire l'arbre
    tree = await build_category_tree(list(categories))

    # Convertir en schéma de réponse avec enfants
    async def convert_to_response(cat: Category) -> CategoryWithChildren:
        children = []
        if hasattr(cat, 'children_list'):
            for child in cat.children_list:
                children.append(await convert_to_response(child))

        product_count = await get_category_product_count(cat.id, db)

        return CategoryWithChildren(
            **cat.__dict__,
            children=children,
            product_count=product_count
        )

    tree_response = []
    for cat in tree:
        tree_response.append(await convert_to_response(cat))

    return CategoryTreeResponse(
        categories=tree_response,
        total_count=len(categories)
    )


@router.get("/{category_id}", response_model=CategoryWithChildren)
async def get_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer une catégorie par son ID avec ses sous-catégories
    """
    category = await get_category_by_id(category_id, db, current_user.store_id)

    # Récupérer les sous-catégories
    result = await db.execute(
        select(Category)
        .where(Category.parent_id == category_id)
        .order_by(Category.display_order, Category.name)
    )
    children = result.scalars().all()

    # Compter les produits
    product_count = await get_category_product_count(category_id, db)

    # Construire la réponse
    children_response = []
    for child in children:
        child_product_count = await get_category_product_count(child.id, db)
        children_response.append(
            CategoryWithChildren(
                **child.__dict__,
                product_count=child_product_count,
                children=[]
            )
        )

    return CategoryWithChildren(
        **category.__dict__,
        children=children_response,
        product_count=product_count
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mettre à jour une catégorie
    """
    category = await get_category_by_id(category_id, db, current_user.store_id)

    # Vérifier que la catégorie parente existe si changée
    if category_data.parent_id and category_data.parent_id != category.parent_id:
        # Ne pas permettre de définir soi-même comme parent
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une catégorie ne peut pas être son propre parent"
            )
        await get_category_by_id(category_data.parent_id, db, current_user.store_id)

    # Vérifier l'unicité du nom si changé
    if category_data.name and category_data.name != category.name:
        result = await db.execute(
            select(Category)
            .where(
                Category.store_id == current_user.store_id,
                Category.name == category_data.name,
                Category.id != category_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une catégorie avec ce nom existe déjà"
            )

    # Mettre à jour les champs
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    force: bool = Query(False, description="Forcer la suppression même avec des produits"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprimer une catégorie

    - Par défaut, refuse de supprimer si des produits sont liés
    - Avec force=true, les produits sont déplacés vers la catégorie parente ou mis à null
    """
    category = await get_category_by_id(category_id, db, current_user.store_id)

    # Vérifier les sous-catégories
    result = await db.execute(
        select(func.count(Category.id))
        .where(Category.parent_id == category_id)
    )
    children_count = result.scalar()

    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer cette catégorie car elle contient {children_count} sous-catégorie(s)"
        )

    # Vérifier les produits
    product_count = await get_category_product_count(category_id, db)

    if product_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cette catégorie contient {product_count} produit(s). Utilisez force=true pour forcer la suppression."
        )

    if product_count > 0 and force:
        # Déplacer les produits vers la catégorie parente ou mettre à null
        await db.execute(
            select(Product)
            .where(Product.category_id == category_id)
            .update({Product.category_id: category.parent_id})
        )

    # Supprimer la catégorie
    await db.delete(category)
    await db.commit()

    return None


@router.get("/{category_id}/stats", response_model=CategoryStats)
async def get_category_stats(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer les statistiques d'une catégorie
    """
    category = await get_category_by_id(category_id, db, current_user.store_id)

    # Compter les produits
    result = await db.execute(
        select(func.count(Product.id))
        .where(Product.category_id == category_id)
    )
    product_count = result.scalar() or 0

    # Compter les produits actifs
    result = await db.execute(
        select(func.count(Product.id))
        .where(Product.category_id == category_id, Product.is_active == True)
    )
    active_product_count = result.scalar() or 0

    # Calculer la valeur totale du stock
    result = await db.execute(
        select(func.sum(Product.stock_quantity_primary * Product.prix_achat))
        .where(Product.category_id == category_id, Product.track_stock == True)
    )
    total_stock_value = result.scalar() or 0.0

    # Compter les sous-catégories
    result = await db.execute(
        select(func.count(Category.id))
        .where(Category.parent_id == category_id)
    )
    children_count = result.scalar() or 0

    return CategoryStats(
        category_id=category.id,
        category_name=category.name,
        product_count=product_count,
        active_product_count=active_product_count,
        total_stock_value=float(total_stock_value),
        children_count=children_count
    )
