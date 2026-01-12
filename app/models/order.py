"""
Modèles Order et OrderItem (Commande et articles de commande)
"""

from sqlalchemy import Column, String, Text, Integer, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Order(BaseModel):
    """Modèle représentant une commande"""

    __tablename__ = "orders"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    cash_register_session_id = Column(UUID(as_uuid=True), ForeignKey("cash_register_sessions.id"), nullable=True)

    # Identification
    order_number = Column(String(50), unique=True, nullable=False, index=True)

    # Informations client
    client_name = Column(String(255))
    client_phone = Column(String(20))

    # Type de commande
    order_type = Column(String(50), nullable=False)  # pos, online, reservation, location
    order_source = Column(String(50), default="pos")  # pos, ecommerce

    # Montants
    subtotal = Column(DECIMAL(15, 2), nullable=False)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    promo_code_discount = Column(DECIMAL(15, 2), default=0)
    loyalty_points_used = Column(Integer, default=0)
    loyalty_discount = Column(DECIMAL(15, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    total_amount = Column(DECIMAL(15, 2), nullable=False)

    # Paiement
    montant_paye = Column(DECIMAL(15, 2), default=0)
    montant_restant = Column(DECIMAL(15, 2), default=0)
    statut_paiement = Column(String(50), default="Non Payer", index=True)
    # Payer, Non Payer, Partiellement, Rembourser, Partiellement Rembourser

    # Statut
    status = Column(String(50), default="pending", index=True)  # pending, confirmed, completed, cancelled

    # Métadonnées
    notes = Column(Text)

    # Relations
    store = relationship("Store", back_populates="orders")
    client = relationship("Client", back_populates="orders")
    created_by_user = relationship("User", back_populates="orders", foreign_keys=[created_by])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="order")
    cash_register_session = relationship("CashRegisterSession", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, number={self.order_number}, total={self.total_amount})>"

    @property
    def is_paid(self) -> bool:
        """Vérifie si la commande est payée"""
        return self.statut_paiement == "Payer"

    @property
    def is_credit_sale(self) -> bool:
        """Vérifie si c'est une vente à crédit"""
        return self.statut_paiement in ["Non Payer", "Partiellement"]

    @property
    def items_count(self) -> int:
        """Retourne le nombre d'articles dans la commande"""
        return len(self.items)


class OrderItem(BaseModel):
    """Modèle représentant un article de commande"""

    __tablename__ = "order_items"

    # Relations
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True)

    # Informations produit (snapshot)
    product_name = Column(String(255), nullable=False)
    variant_name = Column(String(255))
    sku = Column(String(100))

    # Quantité et unité
    quantity = Column(DECIMAL(15, 3), nullable=False)
    unit = Column(String(50), nullable=False)  # primary, secondary

    # Prix
    unit_price = Column(DECIMAL(15, 2), nullable=False)
    discount_amount = Column(DECIMAL(15, 2), default=0)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(15, 2), default=0)
    total_price = Column(DECIMAL(15, 2), nullable=False)

    # Relations
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    variant = relationship("ProductVariant", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product={self.product_name}, qty={self.quantity})>"

    @property
    def subtotal(self) -> float:
        """Calcule le sous-total (prix unitaire * quantité)"""
        return float(self.unit_price) * float(self.quantity)

    @property
    def total(self) -> float:
        """Calcule le total avec taxes et remises"""
        return float(self.total_price)
