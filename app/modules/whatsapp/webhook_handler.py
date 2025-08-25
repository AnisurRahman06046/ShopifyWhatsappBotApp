from fastapi import APIRouter, Request, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.config import settings
from .whatsapp_repository import WhatsAppRepository, ShopifyStoreRepository
from .whatsapp_service import WhatsAppService
from .message_processor import MessageProcessor
import json
import logging
import hmac
import hashlib

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
        # Skip webhook signature verification for now (causes issues in development)
        # await verify_webhook_signature(request)
        
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
    
    # Check billing usage limits
    from app.modules.billing.billing_service import BillingService
    billing_service = BillingService(db)
    usage_check = await billing_service.check_usage_limit(store.id)
    
    if usage_check.get("limit_reached", False):  # Changed default to False
        # Send message about limit reached
        logger.warning(f"Message limit reached for store {store.store_url}")
        logger.warning(f"Usage details: {usage_check}")
        # Optionally send a message to the user about the limit
        # For now, just return to avoid processing
        return
    
    logger.info(f"Processing message for store {store.store_url} - Usage: {usage_check.get('messages_used', 0)}/{usage_check.get('messages_limit', 0)}")
    
    # Initialize services with billing service for usage tracking
    whatsapp_service = WhatsAppService(store, billing_service)
    whatsapp_repo = WhatsAppRepository(db)
    
    # Process each message
    for message in value.get("messages", []):
        from_number = message.get("from")
        message_type = message.get("type")
        
        # Get or create session
        session = await whatsapp_repo.get_or_create_session(from_number, store.store_url)
        
        # Create message processor with database session for product caching
        processor = MessageProcessor(
            whatsapp_service=whatsapp_service,
            shopify_service=None,  # No longer needed - using database
            whatsapp_repo=whatsapp_repo,
            store=store,
            db_session=db  # Pass database session for product repository
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
        
        # Record incoming message usage for billing
        try:
            await billing_service.record_usage(
                store_id=store.id,
                record_type="message_received",
                quantity=1,
                phone_number=from_number,
                message_type=message_type,
                description=f"Incoming {message_type} message"
            )
        except Exception as e:
            logger.error(f"Error recording incoming message usage: {str(e)}")


async def verify_webhook_signature(request: Request):
    """Verify webhook signature for security"""
    
    # Get the raw body
    body = await request.body()
    
    # Get signature from headers (WhatsApp uses X-Hub-Signature-256)
    signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Signature")
    
    # For development/testing, allow webhooks without signatures
    if settings.ENVIRONMENT == "development" or not settings.WEBHOOK_SECRET:
        logger.debug("Webhook signature verification skipped (development mode)")
        return
    
    if not signature:
        logger.warning("Webhook received without signature in production")
        # In production, you might want to be stricter
        return  # For now, allow it
    
    # Verify signature if webhook secret is configured
    if settings.WEBHOOK_SECRET:
        try:
            # Create expected signature
            expected_signature = hmac.new(
                settings.WEBHOOK_SECRET.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Compare signatures
            if not hmac.compare_digest(expected_signature, signature):
                logger.error(f"Invalid webhook signature. Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
                # For now, log but don't block (you can enable blocking later)
                logger.warning("Continuing despite signature mismatch for development")
                return
            
            logger.debug("Webhook signature verified successfully")
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            # Don't block on signature errors during development
            return