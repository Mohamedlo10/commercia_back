"""
Modèle Client
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Client(BaseModel):
    """Modèle représentant un client"""

    __tablename__ = "clients"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)

    # Identification
    code = Column(String(50), unique=True, nullable=False, index=True)

    # Informations de base
    first_name = Column(String(100))
    last_name = Column(String(100))
    company_name = Column(String(255))
    email = Column(String(255), index=True)
    phone = Column(String(20), index=True)
    address = Column(Text)
    city = Column(String(100))

    # Type de client
    client_type = Column(String(50), default="individual")  # individual, company

    # Fidélité et crédit
    loyalty_points = Column(Integer, default=0)
    credit_limit = Column(DECIMAL(15, 2), default=0)
    current_debt = Column(DECIMAL(15, 2), default=0)

    # Métadonnées
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    store = relationship("Store", back_populates="clients")
    orders = relationship("Order", back_populates="client")
    transactions = relationship("Transaction", back_populates="client")
    reservations = relationship("Reservation", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, code={self.code}, name={self.full_name})>"

    @property
    def full_name(self) -> str:
        """Retourne le nom complet du client"""
        if self.client_type == "company":
            return self.company_name or ""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def can_purchase_on_credit(self) -> bool:
        """Vérifie si le client peut acheter à crédit"""
        return self.current_debt < self.credit_limit
