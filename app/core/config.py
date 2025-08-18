# app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:anis1234@localhost/whatsapp_shopify_bot"
    REDIS_HOST: str
    REDIS_PORT: int

    BITCOMMERZ_TOKEN_URL: str
    BITCOMMERZ_CLIENT_ID: str
    BITCOMMERZ_CLIENT_SECRET: str
    REDIRECT_URI: str
    
    # Shopify App Configuration
    SHOPIFY_API_KEY: str
    SHOPIFY_API_SECRET: str
    SHOPIFY_SCOPES: str = "read_products,read_orders,write_orders"
    
    # App Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    
    # Security
    SECRET_KEY: str
    WEBHOOK_SECRET: str = ""
    
    # WhatsApp credentials are now store-specific, configured by each store owner

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
