"""
Schémas Pydantic pour la gestion du stock
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


# ========== ENUMS ==========

class MovementType(str, Enum):
    """Types de mouvements de stock"""
    PURCHASE = "purchase"              # Achat/Approvisionnement
    SALE = "sale"                      # Vente
    RETURN = "return"                  # Retour client
    ADJUSTMENT_IN = "adjustment_in"    # Ajustement positif (inventaire)
    ADJUSTMENT_OUT = "adjustment_out"  # Ajustement négatif (casse, vol, etc.)
    TRANSFER_IN = "transfer_in"        # Transfert entrant
    TRANSFER_OUT = "transfer_out"      # Transfert sortant


# ========== SCHÉMAS DE BASE ==========

class StockMovementBase(BaseModel):
    """Schéma de base pour un mouvement de stock"""
    product_id: UUID = Field(..., description="ID du produit")
    variant_id: Optional[UUID] = Field(None, description="ID de la variante (si applicable)")
    movement_type: MovementType = Field(..., description="Type de mouvement")
    quantity: float = Field(..., gt=0, description="Quantité (positif)")
    unit: str = Field(..., description="Unité (pièce, kg, etc.)")
    reference: Optional[str] = Field(None, max_length=200, description="Référence (numéro de commande, etc.)")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes sur le mouvement")


# ========== SCHÉMAS CRUD ==========

class StockMovementCreate(StockMovementBase):
    """Schéma pour créer un mouvement de stock"""
    store_id: UUID = Field(..., description="ID du magasin")
    order_id: Optional[UUID] = Field(None, description="ID de la commande associée")


class StockAdjustment(BaseModel):
    """Schéma pour un ajustement de stock"""
    product_id: UUID
    variant_id: Optional[UUID] = None
    new_quantity: float = Field(..., ge=0, description="Nouvelle quantité après ajustement")
    reason: str = Field(..., min_length=1, max_length=500, description="Raison de l'ajustement")
    unit: str = Field("pièce", description="Unité")


class StockTransfer(BaseModel):
    """Schéma pour un transfert de stock entre magasins"""
    from_store_id: UUID
    to_store_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: float = Field(..., gt=0)
    unit: str = Field("pièce")
    notes: Optional[str] = None


# ========== SCHÉMAS DE RÉPONSE ==========

class StockMovementResponse(StockMovementBase):
    """Schéma de réponse pour un mouvement de stock"""
    id: UUID
    store_id: UUID
    order_id: Optional[UUID]
    user_id: Optional[UUID] = Field(None, description="Utilisateur qui a créé le mouvement")
    stock_before: float = Field(..., description="Stock avant le mouvement")
    stock_after: float = Field(..., description="Stock après le mouvement")
    created_at: datetime

    class Config:
        from_attributes = True


class StockMovementWithProduct(StockMovementResponse):
    """Schéma de réponse avec informations produit"""
    product_name: str
    product_sku: Optional[str]
    variant_name: Optional[str] = None


class StockMovementListResponse(BaseModel):
    """Schéma de réponse pour une liste paginée de mouvements"""
    items: List[StockMovementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== SCHÉMAS POUR LE STOCK ACTUEL ==========

class ProductStockInfo(BaseModel):
    """Informations sur le stock d'un produit"""
    product_id: UUID
    product_name: str
    product_sku: Optional[str]
    category_name: Optional[str]

    # Stock
    stock_quantity_primary: float
    primary_unit: str
    stock_quantity_secondary: float = 0
    secondary_unit: Optional[str] = None

    # Seuils
    stock_alert_threshold: float
    is_below_threshold: bool
    stock_status: str  # "in_stock", "low_stock", "out_of_stock"

    # Valeur
    cost_price: float
    total_stock_value: float  # stock_quantity * cost_price

    # Métadonnées
    last_movement_date: Optional[datetime]
    has_variants: bool
    track_stock: bool


class VariantStockInfo(BaseModel):
    """Informations sur le stock d'une variante"""
    variant_id: UUID
    product_id: UUID
    product_name: str
    variant_attributes: dict
    stock_quantity: float
    stock_alert_threshold: float
    is_below_threshold: bool
    cost_price: float
    total_stock_value: float
    last_movement_date: Optional[datetime]


class LowStockAlert(BaseModel):
    """Alerte de stock faible"""
    product_id: UUID
    variant_id: Optional[UUID]
    product_name: str
    variant_name: Optional[str]
    current_stock: float
    alert_threshold: float
    shortage: float  # alert_threshold - current_stock
    unit: str


class StockSummary(BaseModel):
    """Résumé global du stock"""
    total_products: int
    products_in_stock: int
    products_low_stock: int
    products_out_of_stock: int
    total_stock_value: float
    products_with_variants: int


# ========== SCHÉMAS POUR INVENTAIRE ==========

class InventoryItem(BaseModel):
    """Item d'inventaire"""
    product_id: UUID
    variant_id: Optional[UUID] = None
    expected_quantity: float
    actual_quantity: float = Field(..., ge=0, description="Quantité réelle comptée")
    difference: float = Field(description="Différence (actual - expected)")
    notes: Optional[str] = None


class InventoryCreate(BaseModel):
    """Schéma pour créer un inventaire"""
    store_id: UUID
    items: List[InventoryItem]
    notes: Optional[str] = None


class InventoryResult(BaseModel):
    """Résultat d'un inventaire"""
    inventory_id: UUID
    items_count: int
    adjustments_made: int
    total_difference_value: float
    created_at: datetime


# ========== SCHÉMAS POUR RAPPORTS ==========

class StockMovementReport(BaseModel):
    """Rapport de mouvements de stock sur une période"""
    period_start: datetime
    period_end: datetime
    total_movements: int
    movements_by_type: dict  # {type: count}
    total_value_in: float
    total_value_out: float
    net_value: float


class ProductStockHistory(BaseModel):
    """Historique du stock d'un produit"""
    product_id: UUID
    product_name: str
    movements: List[StockMovementResponse]
    current_stock: float
    min_stock_period: float
    max_stock_period: float
    average_stock_period: float
