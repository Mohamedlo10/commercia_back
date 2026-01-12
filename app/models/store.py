"""
Modèle Store (Magasin)
"""

from sqlalchemy import Column, String, Text, Boolean, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Store(BaseModel):
    """Modèle représentant un magasin"""

    __tablename__ = "stores"

    # Informations de base
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    siret = Column(String(50))
    logo_url = Column(Text)

    # Configuration
    currency = Column(String(3), default="XOF")
    timezone = Column(String(50), default="Africa/Abidjan")
    vat_rate = Column(DECIMAL(5, 2), default=0.00)
    tax_config = Column(JSONB, default={})
    settings = Column(JSONB, default={})

    # Statut
    is_active = Column(Boolean, default=True)

    # Relations
    users = relationship("User", back_populates="store", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="store", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="store", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Store(id={self.id}, name={self.name})>"
