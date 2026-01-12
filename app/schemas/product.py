"""
Schémas Pydantic pour les produits et variantes
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class ProductType(str):
    """Types de produits"""
    PHYSICAL = "physical"  # Produit physique
    SERVICE = "service"    # Service
    DIGITAL = "digital"    # Produit numérique


class ProductStatus(str):
    """Statuts des produits"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


# ============ SCHÉMAS POUR VARIANTES ============

class ProductVariantBase(BaseModel):
    """Schéma de base pour une variante de produit"""
    sku: Optional[str] = Field(None, max_length=100, description="SKU unique de la variante")
    barcode: Optional[str] = Field(None, max_length=100, description="Code-barres")
    attributes: dict = Field(..., description="Attributs de la variante (ex: {\"couleur\": \"Rouge\", \"taille\": \"M\"})")
    price: float = Field(..., gt=0, description="Prix de vente")
    cost_price: Optional[float] = Field(None, ge=0, description="Prix d'achat")
    stock_quantity: float = Field(0, ge=0, description="Quantité en stock")
    sku: Optional[str] = Field(None, max_length=100, description="Code SKU spécifique à cette variante")
    barcode: Optional[str] = Field(None, max_length=100, description="Code-barres de la variante")
    image_url: Optional[str] = None
    is_active: bool = True


class ProductVariantCreate(BaseModel):
    """Schéma pour créer une variante de produit"""
    name: str = Field(..., min_length=1, max_length=200)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    price: float = Field(..., gt=0, description="Prix de vente")
    cost_price: Optional[float] = Field(None, ge=0, description="Prix de revient")
    attributes: Optional[dict] = Field(default_factory=dict, description="Attributs de la variante (couleur, taille, etc.)")
    stock_quantity: float = Field(0, ge=0)
    stock_alert_threshold: Optional[float] = Field(10, ge=0)
    is_active: bool = True


class ProductVariantUpdate(BaseModel):
    """Schéma pour mettre à jour une variante de produit"""
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    attributes: Optional[dict] = None
    price_adjustment: Optional[float] = None
    stock_quantity: Optional[float] = Field(None, ge=0)
    stock_alert_threshold: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    """Schéma de réponse pour une variante de produit"""
    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== SCHÉMAS PRODUITS ==========

class ProductBase(BaseModel):
    """Schéma de base pour un produit"""
    name: str = Field(..., min_length=1, max_length=200, description="Nom du produit")
    description: Optional[str] = Field(None, max_length=2000, description="Description du produit")
    sku: Optional[str] = Field(None, max_length=100, description="SKU/Référence produit")
    barcode: Optional[str] = Field(None, max_length=100, description="Code-barres")
    category_id: Optional[UUID] = Field(None, description="ID de la catégorie")

    # Prix
    prix_achat: float = Field(..., gt=0, description="Prix d'achat HT")
    prix_vente: float = Field(..., gt=0, description="Prix de vente HT")
    prix_vente_ttc: Optional[float] = Field(None, description="Prix TTC (calculé automatiquement)")
    tva_rate: float = Field(0, ge=0, le=100, description="Taux de TVA en pourcentage")

    # Multi-unités
    has_multiple_units: bool = Field(False, description="Produit avec plusieurs unités?")
    primary_unit: str = Field("pièce", max_length=50, description="Unité primaire")
    secondary_unit: Optional[str] = Field(None, max_length=50, description="Unité secondaire")
    units_per_primary: int = Field(1, ge=1, description="Nombre d'unités secondaires par unité primaire")

    # Gestion du stock
    track_stock: bool = Field(True, description="Suivre le stock?")
    stock_alert_threshold: float = Field(10, ge=0, description="Seuil d'alerte de stock")

    # Variantes
    has_variants: bool = Field(False, description="Le produit a-t-il des variantes?")
    variant_attributes: Optional[dict] = Field(None, description="Attributs des variantes (ex: {\"taille\": [\"S\", \"M\", \"L\"]})")


# Schéma de création
class ProductCreate(ProductBase):
    """Schéma pour créer un produit"""
    store_id: UUID = Field(..., description="ID du magasin")
    category_id: Optional[UUID] = Field(None, description="ID de la catégorie")


# Schéma de mise à jour
class ProductUpdate(BaseModel):
    """Schéma pour mettre à jour un produit"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)

    # Prix
    purchase_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    discount_price: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)

    # Multi-unités
    has_multiple_units: Optional[bool] = None
    primary_unit: Optional[str] = None
    secondary_unit: Optional[str] = None
    units_per_primary: Optional[int] = Field(None, ge=1)
    price_per_secondary_unit: Optional[float] = Field(None, ge=0)

    # Stock
    track_stock: Optional[bool] = None
    stock_alert_threshold: Optional[float] = Field(None, ge=0)

    # Variantes
    has_variants: Optional[bool] = None

    # Autres
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


# Schéma de réponse simple
class ProductResponse(ProductBase):
    """Schéma de réponse pour un produit"""
    id: UUID
    store_id: UUID
    category_id: Optional[UUID] = None

    # Statut calculé
    is_in_stock: bool = Field(description="Le produit est-il en stock?")
    stock_status: str = Field(description="Statut du stock: 'in_stock', 'low_stock', 'out_of_stock'")

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Schéma de réponse avec relations
class ProductWithRelations(ProductResponse):
    """Schéma de réponse avec catégorie et variantes"""
    category: Optional['CategoryResponse'] = None
    variants: List[ProductVariantResponse] = Field(default_factory=list)


# Schéma pour la liste paginée
class ProductListResponse(BaseModel):
    """Schéma de réponse pour une liste paginée de produits"""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Schéma pour les filtres de recherche
class ProductFilter(BaseModel):
    """Filtres de recherche de produits"""
    search: Optional[str] = Field(None, description="Recherche dans nom, code, description")
    category_id: Optional[UUID] = Field(None, description="Filtrer par catégorie")
    is_active: Optional[bool] = Field(None, description="Filtrer par statut actif")
    track_stock: Optional[bool] = Field(None, description="Filtrer les produits suivis en stock")
    has_variants: Optional[bool] = Field(None, description="Filtrer les produits avec variantes")
    min_price: Optional[float] = Field(None, ge=0, description="Prix minimum")
    max_price: Optional[float] = Field(None, ge=0, description="Prix maximum")
    in_stock_only: Optional[bool] = Field(False, description="Afficher uniquement les produits en stock")
    sort_by: Optional[str] = Field("created_at", description="Tri: name, price, stock, created_at")
    sort_order: Optional[str] = Field("desc", description="Ordre: asc, desc")


# Import pour éviter les erreurs de référence circulaire
from app.schemas.category import CategoryResponse

ProductWithRelations.model_rebuild()
