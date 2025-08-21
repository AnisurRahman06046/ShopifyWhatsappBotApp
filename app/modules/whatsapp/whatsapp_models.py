from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, nullable=False, unique=True)
    shopify_store_url = Column(String, nullable=False)
    session_state = Column(String, default="browsing")  # browsing, cart, checkout
    cart_data = Column(Text)  # JSON string of cart items
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ShopifyStore(Base):
    __tablename__ = "shopify_stores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_url = Column(String, nullable=False, unique=True)
    access_token = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    whatsapp_enabled = Column(Boolean, default=False)
    
    # Meta Business API credentials (store-specific)
    whatsapp_token = Column(String, nullable=True)
    whatsapp_phone_number_id = Column(String, nullable=True)
    whatsapp_verify_token = Column(String, nullable=True)
    whatsapp_business_account_id = Column(String, nullable=True)
    
    welcome_message = Column(Text, default="👋 Welcome! Click 'Browse Products' to start shopping.")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("StoreSubscription", back_populates="store", uselist=False)