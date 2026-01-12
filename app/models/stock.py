"""
Modèle StockMovement (Mouvement de stock)
"""

from sqlalchemy import Column, String, Text, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class StockMovement(BaseModel):
    """Modèle représentant un mouvement de stock"""

    __tablename__ = "stock_movements"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Type de mouvement
    movement_type = Column(String(50), nullable=False, index=True)
    # in, out, adjustment, return, transfer

    # Quantité
    quantity = Column(DECIMAL(15, 3), nullable=False)
    unit = Column(String(50), nullable=False)  # primary, secondary

    # Référence (commande, remboursement, manuel, import)
    reference_type = Column(String(50))  # order, refund, manual, import
    reference_id = Column(UUID(as_uuid=True))

    # Métadonnées
    reason = Column(Text)
    notes = Column(Text)

    # Relations
    store = relationship("Store")
    product = relationship("Product", back_populates="stock_movements")
    variant = relationship("ProductVariant", back_populates="stock_movements")
    user = relationship("User")

    def __repr__(self):
        return f"<StockMovement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"

    @property
    def is_incoming(self) -> bool:
        """Vérifie si c'est une entrée de stock"""
        return self.movement_type in ["in", "return", "adjustment"]

    @property
    def is_outgoing(self) -> bool:
        """Vérifie si c'est une sortie de stock"""
        return self.movement_type in ["out", "transfer"]
