from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .whatsapp_models import WhatsAppSession, ShopifyStore
import json
from typing import Optional


class WhatsAppRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(self, phone_number: str, store_url: str) -> WhatsAppSession:
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.phone_number == phone_number)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            session = WhatsAppSession(
                phone_number=phone_number,
                shopify_store_url=store_url,
                session_state="browsing",
                cart_data=json.dumps([])
            )
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
        
        return session

    async def update_session_state(self, phone_number: str, state: str):
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.phone_number == phone_number)
        )
        session = result.scalar_one_or_none()
        if session:
            session.session_state = state
            await self.db.commit()

    async def update_cart(self, phone_number: str, cart_data: list):
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.phone_number == phone_number)
        )
        session = result.scalar_one_or_none()
        if session:
            session.cart_data = json.dumps(cart_data)
            await self.db.commit()

    async def get_cart(self, phone_number: str) -> list:
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.phone_number == phone_number)
        )
        session = result.scalar_one_or_none()
        if session and session.cart_data:
            return json.loads(session.cart_data)
        return []


class ShopifyStoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_store(self, store_url: str, access_token: str, shop_name: str) -> ShopifyStore:
        store = ShopifyStore(
            store_url=store_url,
            access_token=access_token,
            shop_name=shop_name
        )
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def get_store_by_url(self, store_url: str) -> Optional[ShopifyStore]:
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.store_url == store_url)
        )
        return result.scalar_one_or_none()

    async def update_store_config(self, store_url: str, welcome_message: str = None, whatsapp_enabled: bool = None):
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.store_url == store_url)
        )
        store = result.scalar_one_or_none()
        if store:
            if welcome_message is not None:
                store.welcome_message = welcome_message
            if whatsapp_enabled is not None:
                store.whatsapp_enabled = whatsapp_enabled
            await self.db.commit()
    
    async def get_store_by_phone_number(self, phone_number_id: str) -> Optional[ShopifyStore]:
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.whatsapp_phone_number_id == phone_number_id)
        )
        return result.scalar_one_or_none()
    
    async def update_whatsapp_config(self, store_url: str, config: dict):
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.store_url == store_url)
        )
        store = result.scalar_one_or_none()
        if store:
            store.whatsapp_token = config.get("whatsapp_token")
            store.whatsapp_phone_number_id = config.get("whatsapp_phone_number_id")
            store.whatsapp_verify_token = config.get("whatsapp_verify_token")
            store.whatsapp_business_account_id = config.get("whatsapp_business_account_id")
            store.welcome_message = config.get("welcome_message", store.welcome_message)
            store.whatsapp_enabled = True
            await self.db.commit()
            return store
        return None

    # GDPR Compliance Methods
    
    async def mark_store_uninstalled(self, store_url: str):
        """Mark store as uninstalled instead of deleting for compliance"""
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.store_url == store_url)
        )
        store = result.scalar_one_or_none()
        if store:
            store.whatsapp_enabled = False
            store.uninstalled_at = "NOW()"  # You might want to add this field to model
            await self.db.commit()
    
    async def clear_store_credentials(self, store_url: str):
        """Clear sensitive credentials on uninstall"""
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.store_url == store_url)
        )
        store = result.scalar_one_or_none()
        if store:
            # Clear WhatsApp credentials but keep basic store info for compliance
            store.whatsapp_token = None
            store.whatsapp_verify_token = None
            store.access_token = None  # Clear Shopify access token too
            await self.db.commit()
    
    async def get_customer_data(self, shop_domain: str, customer_id: str = None, customer_phone: str = None) -> dict:
        """Get customer data for GDPR compliance"""
        
        # Get customer sessions by phone number
        sessions = []
        if customer_phone:
            result = await self.db.execute(
                select(WhatsAppSession).where(WhatsAppSession.phone_number == customer_phone)
            )
            sessions = result.scalars().all()
        
        return {
            "sessions": [
                {
                    "phone_number": session.phone_number,
                    "store": session.shopify_store_url,
                    "session_state": session.session_state,
                    "created_at": str(session.created_at),
                    "updated_at": str(session.updated_at)
                }
                for session in sessions
            ],
            "cart_data": [json.loads(session.cart_data) for session in sessions if session.cart_data],
            "preferences": {}  # Add if you store user preferences
        }
    
    async def delete_customer_data(self, shop_domain: str, customer_id: str = None, customer_phone: str = None) -> int:
        """Delete customer data for GDPR compliance"""
        
        deleted_count = 0
        
        if customer_phone:
            # Delete WhatsApp sessions for this customer
            result = await self.db.execute(
                select(WhatsAppSession).where(WhatsAppSession.phone_number == customer_phone)
            )
            sessions = result.scalars().all()
            
            for session in sessions:
                await self.db.delete(session)
                deleted_count += 1
            
            await self.db.commit()
        
        return deleted_count
    
    async def delete_shop_data(self, shop_domain: str) -> int:
        """Delete all shop data for GDPR compliance"""
        
        deleted_count = 0
        
        # Delete all WhatsApp sessions for this shop
        result = await self.db.execute(
            select(WhatsAppSession).where(WhatsAppSession.shopify_store_url == shop_domain)
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            await self.db.delete(session)
            deleted_count += 1
        
        # Delete the store record
        result = await self.db.execute(
            select(ShopifyStore).where(ShopifyStore.store_url == shop_domain)
        )
        store = result.scalar_one_or_none()
        
        if store:
            await self.db.delete(store)
            deleted_count += 1
        
        await self.db.commit()
        
        return deleted_count