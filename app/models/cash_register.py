"""
Modèles CashRegisterSession et CashRegisterDetail
"""

from sqlalchemy import Column, String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CashRegisterSession(BaseModel):
    """Modèle représentant une session de caisse"""

    __tablename__ = "cash_register_sessions"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    opened_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Identification
    session_number = Column(String(50), unique=True, nullable=False, index=True)

    # Montants
    opening_amount = Column(DECIMAL(15, 2), nullable=False)
    closing_amount = Column(DECIMAL(15, 2))
    expected_amount = Column(DECIMAL(15, 2))
    difference = Column(DECIMAL(15, 2))

    # Statut
    status = Column(String(50), default="open", index=True)  # open, closed

    # Dates
    opened_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))

    # Notes
    notes = Column(Text)
    closing_notes = Column(Text)

    # Relations
    store = relationship("Store")
    opened_by_user = relationship("User", foreign_keys=[opened_by])
    closed_by_user = relationship("User", foreign_keys=[closed_by])
    details = relationship("CashRegisterDetail", back_populates="session", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="cash_register_session")
    transactions = relationship("Transaction", back_populates="cash_register_session")

    def __repr__(self):
        return f"<CashRegisterSession(id={self.id}, number={self.session_number}, status={self.status})>"

    @property
    def is_open(self) -> bool:
        """Vérifie si la session est ouverte"""
        return self.status == "open"

    @property
    def has_discrepancy(self) -> bool:
        """Vérifie s'il y a une différence entre attendu et réel"""
        if self.difference is None:
            return False
        return abs(float(self.difference)) > 0.01


class CashRegisterDetail(BaseModel):
    """Modèle représentant les détails de caisse par méthode de paiement"""

    __tablename__ = "cash_register_details"

    # Relations
    session_id = Column(UUID(as_uuid=True), ForeignKey("cash_register_sessions.id", ondelete="CASCADE"), nullable=False)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("payment_methods.id"), nullable=False)

    # Montants
    opening_amount = Column(DECIMAL(15, 2), default=0)
    total_in = Column(DECIMAL(15, 2), default=0)  # entrées (ventes, dépôts)
    total_out = Column(DECIMAL(15, 2), default=0)  # sorties (remboursements, retraits)
    expected_closing = Column(DECIMAL(15, 2), default=0)
    actual_closing = Column(DECIMAL(15, 2))
    difference = Column(DECIMAL(15, 2))

    # Relations
    session = relationship("CashRegisterSession", back_populates="details")
    payment_method = relationship("PaymentMethod")

    def __repr__(self):
        return f"<CashRegisterDetail(id={self.id}, session={self.session_id})>"

    @property
    def calculated_expected(self) -> float:
        """Calcule le montant attendu"""
        return float(self.opening_amount) + float(self.total_in) - float(self.total_out)
