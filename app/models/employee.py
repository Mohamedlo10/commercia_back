"""
Modèle Employee (Employé)
Extension du modèle User avec informations RH
"""

from sqlalchemy import Column, String, Text, Date, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Employee(BaseModel):
    """Modèle représentant un employé avec informations RH"""

    __tablename__ = "employees"

    # Relations
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)

    # Informations personnelles
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    national_id = Column(String(50))
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)

    # Informations professionnelles
    position = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    base_salary = Column(DECIMAL(15, 2))

    # Statut
    status = Column(String(50), default="active")  # active, on_leave, terminated

    # Notes
    notes = Column(Text)

    # Relations
    user = relationship("User", back_populates="employee")
    store = relationship("Store")

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.first_name} {self.last_name})>"

    @property
    def full_name(self) -> str:
        """Retourne le nom complet"""
        return f"{self.first_name} {self.last_name}"
