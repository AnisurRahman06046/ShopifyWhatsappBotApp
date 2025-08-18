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