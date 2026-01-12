"""
Modèle de base pour tous les modèles SQLAlchemy
Contient les champs communs et utilitaires
"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
import uuid

from app.core.database import Base


class TimestampMixin:
    """Mixin pour ajouter created_at et updated_at"""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UUIDMixin:
    """Mixin pour ajouter un ID UUID"""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Modèle de base abstrait avec ID UUID et timestamps
    """
    __abstract__ = True

    def dict(self):
        """Convertit le modèle en dictionnaire"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
