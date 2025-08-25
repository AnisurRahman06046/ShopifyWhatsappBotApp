# app/modules/billing/billing_models.py
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class BillingPlan(Base):
    """Available billing plans for the app"""
    __tablename__ = "billing_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    interval = Column(String(20), default="EVERY_30_DAYS")  # EVERY_30_DAYS, ANNUAL
    trial_days = Column(Integer, default=7)
    
    # Plan features
    messages_limit = Column(Integer, nullable=False)  # Monthly message limit
    stores_limit = Column(Integer, default=1)  # Number of stores allowed
    features = Column(Text)  # JSON string of features
    
    # Shopify plan details
    test = Column(Boolean, default=False)  # Test charge for development
    capped_amount = Column(Float, nullable=True)  # For usage-based billing
    terms = Column(String(255), nullable=True)  # Plan terms description
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("StoreSubscription", back_populates="plan")


class StoreSubscription(Base):
    """Store subscription records"""
    __tablename__ = "store_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("billing_plans.id"))
    
    # Shopify charge details
    shopify_charge_id = Column(String(255), unique=True, nullable=True)
    shopify_recurring_charge_id = Column(String(255), unique=True, nullable=True)
    
    # Subscription status
    status = Column(String(50), default="pending")  # pending, active, cancelled, expired
    trial_ends_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    messages_used = Column(Integer, default=0)
    messages_reset_at = Column(DateTime, default=datetime.utcnow)
    
    # Billing details
    confirmation_url = Column(Text, nullable=True)  # Shopify confirmation URL
    last_payment_at = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("ShopifyStore", back_populates="subscription")
    plan = relationship("BillingPlan", back_populates="subscriptions")
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")


class UsageRecord(Base):
    """Track usage for billing purposes"""
    __tablename__ = "usage_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("store_subscriptions.id", ondelete="CASCADE"))
    
    # Usage details
    record_type = Column(String(50), nullable=False)  # message_sent, product_synced, etc.
    quantity = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    
    # WhatsApp specific
    phone_number = Column(String(50), nullable=True)
    message_type = Column(String(50), nullable=True)  # text, image, interactive, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription = relationship("StoreSubscription", back_populates="usage_records")


class BillingEvent(Base):
    """Log billing-related events"""
    __tablename__ = "billing_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"))
    
    event_type = Column(String(50), nullable=False)  # charge_created, charge_activated, charge_cancelled, etc.
    shopify_charge_id = Column(String(255), nullable=True)
    
    # Event details
    status = Column(String(50), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    
    # Request/Response data
    request_data = Column(Text, nullable=True)  # JSON
    response_data = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    store = relationship("ShopifyStore")


class FreeUsageTracking(Base):
    """Track usage for free tier users (no Shopify subscription)"""
    __tablename__ = "free_usage_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("shopify_stores.id", ondelete="CASCADE"))
    
    # Usage counters
    messages_used = Column(Integer, default=0)
    messages_limit = Column(Integer, default=100)  # Free tier limit
    messages_reset_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("ShopifyStore")