"""
Modèle Product (Produit)
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Product(BaseModel):
    """Modèle représentant un produit"""

    __tablename__ = "products"

    # Relations
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Identification
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    product_type = Column(String(50), nullable=False, index=True)  # retail, clothing, electronics, hardware, service

    # Prix
    purchase_price = Column(DECIMAL(15, 2))
    selling_price = Column(DECIMAL(15, 2), nullable=False)
    wholesale_price = Column(DECIMAL(15, 2))

    # Gestion des unités multiples
    has_multiple_units = Column(Boolean, default=False)
    primary_unit = Column(String(50), default="pièce")  # carton, boîte, etc.
    secondary_unit = Column(String(50))  # pièce, unité
    units_per_primary = Column(Integer, default=1)  # nombre d'unités secondaires dans une unité primaire

    # Stock
    track_stock = Column(Boolean, default=True)
    stock_quantity_primary = Column(DECIMAL(15, 3), default=0)
    stock_quantity_secondary = Column(DECIMAL(15, 3), default=0)
    stock_alert_threshold = Column(DECIMAL(15, 3), default=10)

    # Variantes
    has_variants = Column(Boolean, default=False)
    variant_attributes = Column(JSONB)  # {"size": ["S", "M", "L"], "color": ["red", "blue"]}

    # Attributs spécifiques par type
    attributes = Column(JSONB, default={})

    # Images
    images = Column(JSONB, default=[])  # ["url1", "url2"]

    # Taxes
    tax_rate = Column(DECIMAL(5, 2), default=0)

    # E-commerce
    is_published_online = Column(Boolean, default=False)
    online_description = Column(Text)

    # Métadonnées
    barcode = Column(String(100), index=True)
    brand = Column(String(100))
    supplier_reference = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)

    # Relations
    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name})>"

    @property
    def is_in_stock(self) -> bool:
        """Vérifie si le produit est en stock"""
        if not self.track_stock:
            return True
        if self.has_variants:
            return any(v.stock_quantity > 0 for v in self.variants)
        return self.stock_quantity_primary > 0 or self.stock_quantity_secondary > 0

    @property
    def total_stock(self) -> float:
        """Retourne le stock total en unité primaire"""
        if self.has_variants:
            return sum(v.stock_quantity for v in self.variants)
        return float(self.stock_quantity_primary)

    @property
    def is_low_stock(self) -> bool:
        """Vérifie si le stock est bas"""
        if not self.track_stock:
            return False
        return self.total_stock <= float(self.stock_alert_threshold)


class ProductVariant(BaseModel):
    """Modèle représentant une variante de produit"""

    __tablename__ = "product_variants"

    # Relations
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    # Identification
    sku = Column(String(100), unique=True, nullable=False, index=True)
    variant_name = Column(String(255), nullable=False)  # "Rouge - M"
    attributes = Column(JSONB, nullable=False)  # {"color": "red", "size": "M"}

    # Prix spécifique (optionnel)
    selling_price = Column(DECIMAL(15, 2))
    purchase_price = Column(DECIMAL(15, 2))

    # Stock spécifique
    stock_quantity = Column(DECIMAL(15, 3), default=0)
    stock_alert_threshold = Column(DECIMAL(15, 3), default=5)

    # Métadonnées
    barcode = Column(String(100), index=True)
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relations
    product = relationship("Product", back_populates="variants")
    order_items = relationship("OrderItem", back_populates="variant")
    stock_movements = relationship("StockMovement", back_populates="variant")

    def __repr__(self):
        return f"<ProductVariant(id={self.id}, sku={self.sku}, name={self.variant_name})>"

    @property
    def is_in_stock(self) -> bool:
        """Vérifie si la variante est en stock"""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        """Vérifie si le stock est bas"""
        return self.stock_quantity <= self.stock_alert_threshold

    @property
    def effective_selling_price(self) -> float:
        """Retourne le prix de vente effectif (de la variante ou du produit parent)"""
        if self.selling_price:
            return float(self.selling_price)
        return float(self.product.selling_price)
