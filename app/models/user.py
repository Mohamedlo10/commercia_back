"""
Modèle User (Utilisateur)
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """Modèle représentant un utilisateur du système"""

    __tablename__ = "users"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)

    # Authentification
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Rôle et permissions
    role = Column(String(50), nullable=False)  # admin, manager, cashier, seller
    is_active = Column(Boolean, default=True)

    # Dernière connexion
    last_login = Column(DateTime(timezone=True))

    # Relations
    store = relationship("Store", back_populates="users")
    employee = relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="created_by_user", foreign_keys="Order.created_by")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est admin"""
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        """Vérifie si l'utilisateur est manager"""
        return self.role in ["admin", "manager"]
