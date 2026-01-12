"""
Schémas Pydantic pour les clients
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator
import re


# ========== SCHÉMAS DE BASE ==========

class ClientBase(BaseModel):
    """Schéma de base pour un client"""
    first_name: str = Field(..., min_length=1, max_length=100, description="Prénom")
    last_name: str = Field(..., min_length=1, max_length=100, description="Nom")
    email: Optional[EmailStr] = Field(None, description="Email")
    phone: str = Field(..., min_length=8, max_length=20, description="Téléphone")
    address: Optional[str] = Field(None, max_length=500, description="Adresse")
    city: Optional[str] = Field(None, max_length=100, description="Ville")
    country: str = Field("Sénégal", max_length=100, description="Pays")

    # Programme de fidélité
    loyalty_tier: str = Field("bronze", description="Niveau de fidélité: bronze, silver, gold, platinum")

    # Crédit client
    credit_limit: float = Field(0, ge=0, description="Limite de crédit autorisée")

    # Notes
    notes: Optional[str] = Field(None, max_length=2000, description="Notes sur le client")

    @validator('phone')
    def validate_phone(cls, v):
        """Valide le format du numéro de téléphone"""
        # Retire les espaces et caractères spéciaux
        phone_clean = re.sub(r'[^\d+]', '', v)
        if len(phone_clean) < 8:
            raise ValueError("Le numéro de téléphone doit contenir au moins 8 chiffres")
        return v

    @validator('loyalty_tier')
    def validate_loyalty_tier(cls, v):
        """Valide le niveau de fidélité"""
        allowed_tiers = ['bronze', 'silver', 'gold', 'platinum']
        if v.lower() not in allowed_tiers:
            raise ValueError(f"Niveau de fidélité invalide. Valeurs autorisées: {', '.join(allowed_tiers)}")
        return v.lower()


# ========== SCHÉMAS CRUD ==========

class ClientCreate(ClientBase):
    """Schéma pour créer un client"""
    store_id: UUID = Field(..., description="ID du magasin")


class ClientUpdate(BaseModel):
    """Schéma pour mettre à jour un client"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    loyalty_tier: Optional[str] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone_clean = re.sub(r'[^\d+]', '', v)
            if len(phone_clean) < 8:
                raise ValueError("Le numéro de téléphone doit contenir au moins 8 chiffres")
        return v


# ========== SCHÉMAS DE RÉPONSE ==========

class ClientResponse(ClientBase):
    """Schéma de réponse pour un client"""
    id: UUID
    store_id: UUID
    client_code: str = Field(..., description="Code client unique (ex: CLI-001)")

    # Fidélité
    loyalty_points: int = Field(0, description="Points de fidélité accumulés")

    # Dette et crédit
    total_debt: float = Field(0, description="Dette totale actuelle")

    # Statut
    is_active: bool = True

    # Métadonnées
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_purchase_date: Optional[datetime] = Field(None, description="Date du dernier achat")

    class Config:
        from_attributes = True


class ClientWithStats(ClientResponse):
    """Schéma de réponse avec statistiques complètes"""
    total_orders: int = Field(0, description="Nombre total de commandes")
    total_spent: float = Field(0, description="Montant total dépensé")
    average_order_value: float = Field(0, description="Panier moyen")
    can_purchase_on_credit: bool = Field(description="Peut acheter à crédit?")


# ========== SCHÉMAS DE LISTE ==========

class ClientListResponse(BaseModel):
    """Schéma de réponse pour une liste paginée de clients"""
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ClientFilter(BaseModel):
    """Filtres de recherche de clients"""
    search: Optional[str] = Field(None, description="Recherche dans nom, prénom, email, téléphone, code")
    loyalty_tier: Optional[str] = Field(None, description="Filtrer par niveau de fidélité")
    has_debt: Optional[bool] = Field(None, description="Filtrer les clients avec une dette")
    is_active: Optional[bool] = Field(None, description="Filtrer par statut actif")
    city: Optional[str] = Field(None, description="Filtrer par ville")
    min_loyalty_points: Optional[int] = Field(None, ge=0, description="Points de fidélité minimum")
    sort_by: Optional[str] = Field("created_at", description="Tri: name, points, debt, last_purchase, created_at")
    sort_order: Optional[str] = Field("desc", description="Ordre: asc, desc")


# ========== SCHÉMAS POUR OPÉRATIONS SPÉCIFIQUES ==========

class LoyaltyPointsAdjustment(BaseModel):
    """Schéma pour ajuster les points de fidélité"""
    points: int = Field(..., description="Nombre de points (positif pour ajouter, négatif pour retirer)")
    reason: str = Field(..., min_length=1, max_length=500, description="Raison de l'ajustement")


class DebtPayment(BaseModel):
    """Schéma pour un paiement de dette"""
    amount: float = Field(..., gt=0, description="Montant du paiement")
    payment_method: str = Field(..., description="Méthode de paiement")
    notes: Optional[str] = Field(None, max_length=500, description="Notes sur le paiement")


class ClientStats(BaseModel):
    """Statistiques d'un client"""
    client_id: UUID
    client_name: str
    total_orders: int
    total_spent: float
    total_debt: float
    loyalty_points: int
    loyalty_tier: str
    average_order_value: float
    last_purchase_date: Optional[datetime]
    orders_this_month: int
    spent_this_month: float


# ========== SCHÉMAS POUR HISTORIQUE ==========

class ClientPurchaseHistory(BaseModel):
    """Historique d'achat d'un client"""
    order_id: UUID
    order_number: str
    date: datetime
    total_amount: float
    payment_status: str
    items_count: int


class ClientDebtHistory(BaseModel):
    """Historique de dette d'un client"""
    transaction_id: UUID
    date: datetime
    type: str  # "debt_increase", "debt_payment"
    amount: float
    balance_after: float
    notes: Optional[str]
