"""
Modèle Category (Catégorie de produits)
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Category(BaseModel):
    """Modèle représentant une catégorie de produits"""

    __tablename__ = "categories"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Informations
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(Text)

    # Hiérarchie
    level = Column(Integer, default=0)
    path = Column(String(500))  # Ex: "1/5/12" pour la hiérarchie

    # Statut
    is_active = Column(Boolean, default=True)

    # Relations
    store = relationship("Store", back_populates="categories")
    parent = relationship("Category", remote_side="Category.id", backref="children")
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, level={self.level})>"

    @property
    def full_path(self) -> str:
        """Retourne le chemin complet de la catégorie"""
        if self.path:
            return f"{self.path}/{self.id}"
        return str(self.id)
