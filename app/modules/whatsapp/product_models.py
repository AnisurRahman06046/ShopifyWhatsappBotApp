from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("shopify_stores.id"), nullable=False)
    shopify_product_id = Column(String, nullable=False)  # Shopify's product ID
    title = Column(String, nullable=False)
    description = Column(Text)
    product_type = Column(String)
    vendor = Column(String)
    status = Column(String, default="active")  # active, archived, draft
    handle = Column(String)  # URL handle
    tags = Column(Text)  # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shopify_created_at = Column(DateTime)
    shopify_updated_at = Column(DateTime)
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    store = relationship("ShopifyStore", foreign_keys=[store_id])


class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    shopify_variant_id = Column(String, nullable=False)  # Shopify's variant ID
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float)  # Original price (for discounts)
    sku = Column(String)
    inventory_quantity = Column(Integer, default=0)
    inventory_management = Column(String)  # shopify, blank, etc.
    inventory_policy = Column(String)  # deny, continue
    requires_shipping = Column(Boolean, default=True)
    taxable = Column(Boolean, default=True)
    weight = Column(Float)
    weight_unit = Column(String, default="kg")
    position = Column(Integer, default=1)
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shopify_created_at = Column(DateTime)
    shopify_updated_at = Column(DateTime)
    
    # Relationships
    product = relationship("Product", back_populates="variants")


class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    shopify_image_id = Column(String, nullable=False)  # Shopify's image ID
    image_url = Column(String, nullable=False)  # Shopify CDN URL
    alt_text = Column(String)
    position = Column(Integer, default=1)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="images")


class ProductSyncStatus(Base):
    __tablename__ = "product_sync_status"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("shopify_stores.id"), nullable=False, unique=True)
    last_sync_at = Column(DateTime)
    last_health_check_at = Column(DateTime)
    sync_status = Column(String, default="pending")  # pending, syncing, completed, failed
    total_products = Column(Integer, default=0)
    synced_products = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("ShopifyStore", foreign_keys=[store_id])