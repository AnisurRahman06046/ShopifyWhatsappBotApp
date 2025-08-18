from fastapi import APIRouter, Request, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from .whatsapp_repository import WhatsAppRepository, ShopifyStoreRepository
from .whatsapp_service import WhatsAppService, ShopifyService
from .message_processor import MessageProcessor
import json
import logging

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    db: AsyncSession = Depends(get_async_db)
):
    """Verify webhook for WhatsApp Business API"""
    
    # This will need to verify against store-specific tokens
    # For now, return the challenge to verify the webhook
    if hub_mode == "subscribe":
        # In production, verify the token against stored tokens
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/webhook")
async def receive_message(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Handle incoming WhatsApp messages"""
    
    try:
        data = await request.json()
        
        # Extract message details
        if "entry" not in data:
            return {"status": "ok"}
        
        for entry in data["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Handle different types of updates
                if "messages" in value:
                    await handle_messages(value, db)
                elif "statuses" in value:
                    # Handle status updates (delivered, read, etc.)
                    pass
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_messages(value: dict, db: AsyncSession):
    """Process incoming messages"""
    
    metadata = value.get("metadata", {})
    phone_number_id = metadata.get("phone_number_id")
    
    print(f"[DEBUG] Received phone_number_id: {phone_number_id}")
    
    # Find the store by phone number ID
    store_repo = ShopifyStoreRepository(db)
    store = await store_repo.get_store_by_phone_number(phone_number_id)
    
    print(f"[DEBUG] Found store: {store is not None}")
    if store:
        print(f"[DEBUG] Store URL: {store.store_url}")
        print(f"[DEBUG] WhatsApp enabled: {store.whatsapp_enabled}")
        print(f"[DEBUG] Access token: {store.access_token[:10] if store.access_token else 'None'}...")
    
    if not store or not store.whatsapp_enabled:
        logger.warning(f"Store not found or WhatsApp disabled for phone_number_id: {phone_number_id}")
        return
    
    # Initialize services
    whatsapp_service = WhatsAppService(store)
    shopify_service = ShopifyService(store.store_url, store.access_token)
    whatsapp_repo = WhatsAppRepository(db)
    
    # Process each message
    for message in value.get("messages", []):
        from_number = message.get("from")
        message_type = message.get("type")
        
        # Get or create session
        session = await whatsapp_repo.get_or_create_session(from_number, store.store_url)
        
        # Create message processor
        processor = MessageProcessor(
            whatsapp_service=whatsapp_service,
            shopify_service=shopify_service,
            whatsapp_repo=whatsapp_repo,
            store=store
        )
        
        # Process based on message type
        if message_type == "text":
            text = message.get("text", {}).get("body", "").lower()
            await processor.process_text_message(from_number, text, session)
            
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            await processor.process_interactive_message(from_number, interactive, session)
            
        elif message_type == "button":
            button = message.get("button", {})
            await processor.process_button_response(from_number, button, session)