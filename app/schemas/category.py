"""
Schémas Pydantic pour les catégories de produits
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


# Schémas de base
class CategoryBase(BaseModel):
    """Schéma de base pour une catégorie"""
    name: str = Field(..., min_length=1, max_length=200, description="Nom de la catégorie")
    description: Optional[str] = Field(None, max_length=1000, description="Description de la catégorie")
    parent_id: Optional[UUID] = Field(None, description="ID de la catégorie parente (pour hiérarchie)")
    image_url: Optional[str] = Field(None, max_length=500, description="URL de l'image de la catégorie")
    display_order: int = Field(0, ge=0, description="Ordre d'affichage")
    is_active: bool = Field(True, description="Catégorie active?")


# Schéma de création
class CategoryCreate(CategoryBase):
    """Schéma pour créer une catégorie"""
    store_id: UUID = Field(..., description="ID du magasin")


# Schéma de mise à jour
class CategoryUpdate(BaseModel):
    """Schéma pour mettre à jour une catégorie"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[UUID] = None
    image_url: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


# Schéma de réponse simple (sans relations)
class CategoryResponse(CategoryBase):
    """Schéma de réponse pour une catégorie"""
    id: UUID
    store_id: UUID
    path: Optional[str] = Field(None, description="Chemin hiérarchique de la catégorie")
    level: int = Field(0, description="Niveau dans la hiérarchie (0 = racine)")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schéma de réponse avec sous-catégories
class CategoryWithChildren(CategoryResponse):
    """Schéma de réponse avec les sous-catégories"""
    children: List['CategoryWithChildren'] = Field(default_factory=list, description="Sous-catégories")
    product_count: Optional[int] = Field(0, description="Nombre de produits dans cette catégorie")


# Schéma pour la liste paginée
class CategoryListResponse(BaseModel):
    """Schéma de réponse pour une liste paginée de catégories"""
    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Schéma pour l'arbre hiérarchique
class CategoryTreeResponse(BaseModel):
    """Schéma de réponse pour l'arbre des catégories"""
    categories: List[CategoryWithChildren]
    total_count: int


# Schéma pour les statistiques
class CategoryStats(BaseModel):
    """Statistiques d'une catégorie"""
    category_id: UUID
    category_name: str
    product_count: int
    active_product_count: int
    total_stock_value: float
    children_count: int


# Permet la récursivité pour CategoryWithChildren
CategoryWithChildren.model_rebuild()
