"""
Modèles Reservation et ReservationItem
"""

from sqlalchemy import Column, String, Text, Integer, DECIMAL, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Reservation(BaseModel):
    """Modèle représentant une réservation ou location"""

    __tablename__ = "reservations"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Identification
    reservation_number = Column(String(50), unique=True, nullable=False, index=True)

    # Informations client
    client_name = Column(String(255), nullable=False)
    client_phone = Column(String(20), nullable=False)

    # Type
    reservation_type = Column(String(50), nullable=False)  # service, location

    # Dates
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True))
    duration_hours = Column(DECIMAL(10, 2))

    # Montants
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    caution_amount = Column(DECIMAL(15, 2), default=0)
    amount_paid = Column(DECIMAL(15, 2), default=0)
    amount_remaining = Column(DECIMAL(15, 2), default=0)

    # Statut
    status = Column(String(50), default="pending", index=True)
    # pending, confirmed, in_progress, completed, cancelled
    payment_status = Column(String(50), default="Non Payer")

    # Métadonnées
    notes = Column(Text)

    # Relations
    store = relationship("Store")
    client = relationship("Client", back_populates="reservations")
    order = relationship("Order")
    created_by_user = relationship("User")
    items = relationship("ReservationItem", back_populates="reservation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Reservation(id={self.id}, number={self.reservation_number})>"

    @property
    def is_active(self) -> bool:
        """Vérifie si la réservation est active"""
        return self.status in ["confirmed", "in_progress"]

    @property
    def is_paid(self) -> bool:
        """Vérifie si la réservation est payée"""
        return self.payment_status == "Payer"


class ReservationItem(BaseModel):
    """Modèle représentant un article de réservation"""

    __tablename__ = "reservation_items"

    # Relations
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True)

    # Informations produit
    product_name = Column(String(255), nullable=False)
    quantity = Column(DECIMAL(15, 3), nullable=False)
    unit_price = Column(DECIMAL(15, 2), nullable=False)
    total_price = Column(DECIMAL(15, 2), nullable=False)

    # Relations
    reservation = relationship("Reservation", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")

    def __repr__(self):
        return f"<ReservationItem(id={self.id}, product={self.product_name})>"
