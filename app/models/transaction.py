"""
Modèles Transaction et PaymentMethod
"""

from sqlalchemy import Column, String, Text, Boolean, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PaymentMethod(BaseModel):
    """Modèle représentant une méthode de paiement"""

    __tablename__ = "payment_methods"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)

    # Informations
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # cash, card, mobile_money, check, bank_transfer, credit

    # Configuration
    is_active = Column(Boolean, default=True)
    requires_reference = Column(Boolean, default=False)
    config = Column(JSONB, default={})

    # Relations
    store = relationship("Store")
    transactions = relationship("Transaction", back_populates="payment_method")

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, name={self.name}, type={self.type})>"


class Transaction(BaseModel):
    """Modèle représentant une transaction (paiement, remboursement, etc.)"""

    __tablename__ = "transactions"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("payment_methods.id"), nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    cash_register_session_id = Column(UUID(as_uuid=True), ForeignKey("cash_register_sessions.id"), nullable=True)

    # Type de transaction
    transaction_type = Column(String(50), nullable=False, index=True)
    # sale, refund, expense, deposit, caution, deduction, final_payment

    # Montant
    amount = Column(DECIMAL(15, 2), nullable=False)
    reference = Column(String(255))

    # Statut
    status = Column(String(50), default="pending", index=True)  # pending, completed, failed, cancelled

    # Métadonnées
    notes = Column(Text)

    # Relations
    store = relationship("Store")
    order = relationship("Order", back_populates="transactions")
    client = relationship("Client", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    processed_by_user = relationship("User")
    cash_register_session = relationship("CashRegisterSession", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"

    @property
    def is_payment(self) -> bool:
        """Vérifie si c'est un paiement (entrée d'argent)"""
        return self.transaction_type in ["sale", "deposit", "final_payment"]

    @property
    def is_refund(self) -> bool:
        """Vérifie si c'est un remboursement (sortie d'argent)"""
        return self.transaction_type == "refund"
