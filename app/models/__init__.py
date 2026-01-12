"""
Models package
Importe tous les modèles SQLAlchemy
"""

from app.models.base import Base, BaseModel
from app.models.store import Store
from app.models.user import User
from app.models.employee import Employee
from app.models.client import Client
from app.models.category import Category
from app.models.product import Product, ProductVariant
from app.models.order import Order, OrderItem
from app.models.transaction import Transaction, PaymentMethod
from app.models.stock import StockMovement
from app.models.cash_register import CashRegisterSession, CashRegisterDetail
from app.models.reservation import Reservation, ReservationItem

# Import des autres modèles (à créer)
# from app.models.promo import PromoCode, PromoCodeUsage
# from app.models.audit import AuditLog

__all__ = [
    "Base",
    "BaseModel",
    "Store",
    "User",
    "Employee",
    "Client",
    "Category",
    "Product",
    "ProductVariant",
    "Order",
    "OrderItem",
    "Transaction",
    "PaymentMethod",
    "StockMovement",
    "CashRegisterSession",
    "CashRegisterDetail",
    "Reservation",
    "ReservationItem",
]
