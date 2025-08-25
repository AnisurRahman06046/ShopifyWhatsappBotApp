# app/modules/billing/billing_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx
import json
from app.core.config import settings
from .billing_models import BillingPlan, StoreSubscription, UsageRecord, BillingEvent, FreeUsageTracking
from app.modules.whatsapp.whatsapp_models import ShopifyStore
import logging

logger = logging.getLogger(__name__)


class BillingService:
    """Handle all billing operations with Shopify"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_default_plans(self) -> List[BillingPlan]:
        """Create default billing plans if they don't exist"""
        
        # Check if plans exist
        result = await self.db.execute(select(BillingPlan))
        existing_plans = result.scalars().all()
        
        if existing_plans:
            return existing_plans
        
        # Define default plans matching the pricing routes exactly
        default_plans = [
            {
                "name": "Free",
                "price": 0.00,
                "interval": "EVERY_30_DAYS",
                "trial_days": 0,
                "messages_limit": 100,  # From pricing routes
                "stores_limit": 1,
                "features": json.dumps({
                    "basic_chat": True,
                    "product_browsing": True,
                    "cart_management": True,
                    "checkout": True,
                    "product_sync": True,
                    "welcome_message": True,
                    "support": "community",
                    "analytics": False,
                    "order_tracking": False,
                    "priority_support": False
                }),
                "test": False,
                "terms": "Free plan - 100 messages per month"
            },
            {
                "name": "Basic",  # Changed to match pricing routes
                "price": 4.99,   # Updated to match pricing routes
                "interval": "EVERY_30_DAYS",
                "trial_days": 7,
                "messages_limit": 1000,  # From pricing routes
                "stores_limit": 1,
                "features": json.dumps({
                    "basic_chat": True,
                    "product_browsing": True,
                    "cart_management": True,
                    "checkout": True,
                    "product_sync": True,
                    "welcome_message": True,
                    "enhanced_welcome": True,
                    "order_tracking": True,
                    "support": "email",
                    "analytics": True,
                    "product_collections": True,
                    "order_notifications": True,
                    "priority_support": False
                }),
                "test": False,
                "terms": "Basic plan - 1,000 messages per month"
            },
            {
                "name": "Premium",  # Changed to match pricing routes
                "price": 79.00,     # Updated to match pricing routes
                "interval": "EVERY_30_DAYS",
                "trial_days": 7,
                "messages_limit": 10000,  # From pricing routes
                "stores_limit": 1,
                "features": json.dumps({
                    "basic_chat": True,
                    "product_browsing": True,
                    "cart_management": True,
                    "checkout": True,
                    "product_sync": True,
                    "welcome_message": True,
                    "enhanced_welcome": True,
                    "order_tracking": True,
                    "advanced_analytics": True,
                    "priority_support": True,
                    "abandoned_cart_recovery": True,
                    "advanced_search": True,
                    "customer_segmentation": True,
                    "broadcast_messaging": True,
                    "multi_language": True,
                    "webhooks_api": True,
                    "support": "priority"
                }),
                "test": False,
                "terms": "Premium plan - 10,000 messages per month"
            }
        ]
        
        # Create plans
        created_plans = []
        for plan_data in default_plans:
            plan = BillingPlan(**plan_data)
            self.db.add(plan)
            created_plans.append(plan)
        
        await self.db.commit()
        logger.info(f"Created {len(created_plans)} default billing plans")
        
        return created_plans
    
    async def create_recurring_charge(
        self,
        shop: str,
        access_token: str,
        plan: BillingPlan,
        return_url: str
    ) -> Dict[str, Any]:
        """Create a recurring application charge in Shopify"""
        
        try:
            logger.info(f"Starting charge creation for shop: {shop}")
            
            # Log the billing event
            store_result = await self.db.execute(
                select(ShopifyStore).where(ShopifyStore.store_url == shop)
            )
            store = store_result.scalar_one_or_none()
            
            if not store:
                logger.error(f"Store {shop} not found in billing service")
                raise ValueError(f"Store {shop} not found")
            
            logger.info(f"Found store: {store.shop_name} (ID: {store.id})")
            
            # Prepare the charge data
            charge_data = {
                "recurring_application_charge": {
                    "name": f"WhatsApp Bot - {plan.name} Plan",
                    "price": plan.price,
                    "return_url": return_url,
                    "trial_days": plan.trial_days if plan.price > 0 else 0,
                    "test": plan.test or settings.ENVIRONMENT == "development",
                    "terms": plan.terms
                }
            }
            
            # If there's a capped amount (usage-based billing)
            if plan.capped_amount:
                charge_data["recurring_application_charge"]["capped_amount"] = plan.capped_amount
            
            # Create charge via Shopify API
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            url = f"https://{shop}/admin/api/2024-10/recurring_application_charges.json"
            
            logger.info(f"Making Shopify API call to: {url}")
            logger.info(f"Charge data: {charge_data}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=charge_data)
                
                logger.info(f"Shopify API response: Status {response.status_code}, Body: {response.text[:500]}")
                
                if response.status_code != 201:
                    # Log error event
                    event = BillingEvent(
                        store_id=store.id,
                        event_type="charge_creation_failed",
                        status="error",
                        amount=plan.price,
                        request_data=json.dumps(charge_data),
                        response_data=response.text,
                        error_message=f"Status {response.status_code}"
                    )
                    self.db.add(event)
                    await self.db.commit()
                    
                    raise Exception(f"Failed to create charge: {response.text}")
                
                charge_response = response.json()["recurring_application_charge"]
                
                # Create or update subscription record
                result = await self.db.execute(
                    select(StoreSubscription).where(
                        StoreSubscription.store_id == store.id
                    )
                )
                subscription = result.scalar_one_or_none()
                
                if not subscription:
                    subscription = StoreSubscription(
                        store_id=store.id,
                        plan_id=plan.id
                    )
                    self.db.add(subscription)
                
                # Update subscription with charge details
                subscription.shopify_charge_id = str(charge_response["id"])
                subscription.shopify_recurring_charge_id = str(charge_response["id"])
                subscription.status = "pending"
                subscription.confirmation_url = charge_response["confirmation_url"]
                
                if plan.trial_days > 0 and plan.price > 0:
                    subscription.trial_ends_at = datetime.utcnow() + timedelta(days=plan.trial_days)
                
                # Log success event
                event = BillingEvent(
                    store_id=store.id,
                    event_type="charge_created",
                    shopify_charge_id=str(charge_response["id"]),
                    status="pending",
                    amount=plan.price,
                    request_data=json.dumps(charge_data),
                    response_data=json.dumps(charge_response)
                )
                self.db.add(event)
                
                await self.db.commit()
                
                logger.info(f"Created recurring charge {charge_response['id']} for store {shop}")
                
                return {
                    "charge_id": charge_response["id"],
                    "confirmation_url": charge_response["confirmation_url"],
                    "status": charge_response["status"]
                }
                
        except Exception as e:
            logger.error(f"Error creating recurring charge: {str(e)}")
            raise
    
    async def activate_charge(self, shop: str, charge_id: str, access_token: str) -> bool:
        """Activate a recurring charge after merchant approval"""
        
        try:
            # Get the charge details first
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            url = f"https://{shop}/admin/api/2024-10/recurring_application_charges/{charge_id}.json"
            
            async with httpx.AsyncClient() as client:
                # Get charge details
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to get charge details: {response.text}")
                    return False
                
                charge_data = response.json()["recurring_application_charge"]
                
                # Check if already active
                if charge_data["status"] == "active":
                    logger.info(f"Charge {charge_id} already active")
                else:
                    # Activate the charge
                    activate_url = f"{url}/activate.json"
                    response = await client.post(activate_url, headers=headers)
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to activate charge: {response.text}")
                        return False
                    
                    charge_data = response.json()["recurring_application_charge"]
                
                # Update subscription status
                store_result = await self.db.execute(
                    select(ShopifyStore).where(ShopifyStore.store_url == shop)
                )
                store = store_result.scalar_one_or_none()
                
                if store:
                    result = await self.db.execute(
                        select(StoreSubscription).where(
                            and_(
                                StoreSubscription.store_id == store.id,
                                StoreSubscription.shopify_charge_id == str(charge_id)
                            )
                        )
                    )
                    subscription = result.scalar_one_or_none()
                    
                    if subscription:
                        subscription.status = "active"
                        subscription.activated_at = datetime.utcnow()
                        subscription.next_billing_date = datetime.fromisoformat(
                            charge_data.get("billing_on", datetime.utcnow().isoformat()).replace("Z", "+00:00")
                        )
                        
                        # Log activation event
                        event = BillingEvent(
                            store_id=store.id,
                            event_type="charge_activated",
                            shopify_charge_id=str(charge_id),
                            status="active",
                            response_data=json.dumps(charge_data)
                        )
                        self.db.add(event)
                        
                        await self.db.commit()
                        logger.info(f"Activated subscription for store {shop}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error activating charge: {str(e)}")
            return False
    
    async def activate_free_plan(self, store, plan: BillingPlan) -> bool:
        """Activate free plan for a store without creating Shopify charge"""
        
        try:
            # Check if store already has an active subscription
            existing_subscription = await self.get_store_subscription(store.id)
            
            if existing_subscription and existing_subscription.status == "active":
                logger.info(f"Store {store.store_url} already has active subscription")
                return True
            
            # Create free subscription
            subscription = StoreSubscription(
                store_id=store.id,
                plan_id=plan.id,
                status="active",
                activated_at=datetime.utcnow(),
                messages_used=0,
                messages_reset_at=datetime.utcnow()
            )
            
            self.db.add(subscription)
            
            # Log activation event
            event = BillingEvent(
                store_id=store.id,
                event_type="free_plan_activated",
                status="active"
            )
            self.db.add(event)
            
            await self.db.commit()
            logger.info(f"Activated free plan for store {store.store_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error activating free plan: {str(e)}")
            return False
    
    async def cancel_subscription(self, shop: str, access_token: str) -> bool:
        """Cancel the active subscription for a store"""
        
        try:
            # Get store and subscription
            store_result = await self.db.execute(
                select(ShopifyStore).where(ShopifyStore.store_url == shop)
            )
            store = store_result.scalar_one_or_none()
            
            if not store:
                return False
            
            result = await self.db.execute(
                select(StoreSubscription).where(
                    and_(
                        StoreSubscription.store_id == store.id,
                        StoreSubscription.status == "active"
                    )
                )
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                logger.info(f"No active subscription found for store {shop}")
                return True
            
            # Cancel via Shopify API
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            url = f"https://{shop}/admin/api/2024-10/recurring_application_charges/{subscription.shopify_charge_id}.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)
                
                if response.status_code not in [200, 204]:
                    logger.error(f"Failed to cancel charge: {response.text}")
                    return False
            
            # Update subscription status
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.utcnow()
            
            # Log cancellation event
            event = BillingEvent(
                store_id=store.id,
                event_type="charge_cancelled",
                shopify_charge_id=subscription.shopify_charge_id,
                status="cancelled"
            )
            self.db.add(event)
            
            await self.db.commit()
            logger.info(f"Cancelled subscription for store {shop}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False
    
    async def check_usage_limit(self, store_id: str) -> Dict[str, Any]:
        """Check if store has reached its usage limit based on Shopify subscription"""
        
        try:
            # Get active subscription (created by Shopify billing)
            result = await self.db.execute(
                select(StoreSubscription).where(
                    and_(
                        StoreSubscription.store_id == store_id,
                        StoreSubscription.status == "active"
                    )
                ).options(
                    selectinload(StoreSubscription.plan)
                )
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                # No subscription = Free tier, check free usage tracking
                free_usage = await self._get_or_create_free_usage(store_id)
                
                # Check monthly reset for free tier
                if free_usage.messages_reset_at < datetime.utcnow() - timedelta(days=30):
                    free_usage.messages_used = 0
                    free_usage.messages_reset_at = datetime.utcnow()
                    await self.db.commit()
                
                limit_reached = free_usage.messages_used >= free_usage.messages_limit
                
                return {
                    "has_subscription": False,
                    "limit_reached": limit_reached,
                    "messages_used": free_usage.messages_used,
                    "messages_limit": free_usage.messages_limit,
                    "messages_remaining": max(0, free_usage.messages_limit - free_usage.messages_used),
                    "plan_name": "Free",
                    "reset_date": free_usage.messages_reset_at + timedelta(days=30)
                }
            
            # Check if we need to reset the counter (monthly reset)
            if subscription.messages_reset_at < datetime.utcnow() - timedelta(days=30):
                subscription.messages_used = 0
                subscription.messages_reset_at = datetime.utcnow()
                await self.db.commit()
            
            limit_reached = subscription.messages_used >= subscription.plan.messages_limit
            
            return {
                "has_subscription": True,
                "limit_reached": limit_reached,
                "messages_used": subscription.messages_used,
                "messages_limit": subscription.plan.messages_limit,
                "messages_remaining": max(0, subscription.plan.messages_limit - subscription.messages_used),
                "plan_name": subscription.plan.name,
                "reset_date": subscription.messages_reset_at + timedelta(days=30)
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limit: {str(e)}")
            return {
                "has_subscription": False,
                "limit_reached": True,  # Fail safe - block if error
                "messages_used": 0,
                "messages_limit": 100,
                "messages_remaining": 0,
                "plan_name": "Error",
                "error": str(e)
            }
    
    async def record_usage(
        self,
        store_id: str,
        record_type: str = "message_sent",
        quantity: int = 1,
        **kwargs
    ) -> bool:
        """Record usage for stores with active Shopify subscriptions"""
        
        try:
            # Get active subscription (only exists if user subscribed via Shopify)
            result = await self.db.execute(
                select(StoreSubscription).where(
                    and_(
                        StoreSubscription.store_id == store_id,
                        StoreSubscription.status == "active"
                    )
                )
            )
            subscription = result.scalar_one_or_none()
            
            if subscription:
                # Create usage record for paid subscribers
                usage_record = UsageRecord(
                    subscription_id=subscription.id,
                    record_type=record_type,
                    quantity=quantity,
                    **kwargs
                )
                self.db.add(usage_record)
                
                # Update messages counter for both sent and received messages
                if record_type in ["message_sent", "message_received"]:
                    subscription.messages_used += quantity
                
                await self.db.commit()
                logger.debug(f"Recorded usage for store {store_id}: {record_type} x{quantity}")
                return True
            else:
                # Free tier users - track in separate table
                free_usage = await self._get_or_create_free_usage(store_id)
                if record_type in ["message_sent", "message_received"]:
                    free_usage.messages_used += quantity
                    await self.db.commit()
                    logger.debug(f"Recorded free tier usage for store {store_id}: {record_type} x{quantity}")
                return True
            
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            return False
    
    async def _get_or_create_free_usage(self, store_id: str) -> FreeUsageTracking:
        """Get or create free tier usage tracking for a store"""
        
        result = await self.db.execute(
            select(FreeUsageTracking).where(FreeUsageTracking.store_id == store_id)
        )
        free_usage = result.scalar_one_or_none()
        
        if not free_usage:
            free_usage = FreeUsageTracking(
                store_id=store_id,
                messages_used=0,
                messages_limit=100,  # Free tier limit
                messages_reset_at=datetime.utcnow()
            )
            self.db.add(free_usage)
            await self.db.flush()  # Get the ID
        
        return free_usage
    
    async def get_store_subscription(self, store_id: str) -> Optional[StoreSubscription]:
        """Get the current subscription for a store"""
        
        result = await self.db.execute(
            select(StoreSubscription).where(
                and_(
                    StoreSubscription.store_id == store_id,
                    StoreSubscription.status.in_(["active", "pending"])
                )
            ).options(
                selectinload(StoreSubscription.plan)
            )
        )
        return result.scalar_one_or_none()
    
    async def handle_billing_webhook(self, webhook_data: Dict[str, Any], shop: str) -> bool:
        """Handle billing-related webhooks from Shopify"""
        
        try:
            # Get store
            store_result = await self.db.execute(
                select(ShopifyStore).where(ShopifyStore.store_url == shop)
            )
            store = store_result.scalar_one_or_none()
            
            if not store:
                logger.error(f"Store {shop} not found for billing webhook")
                return False
            
            webhook_topic = webhook_data.get("topic", "")
            
            if "recurring_application_charge" in webhook_topic:
                charge_data = webhook_data.get("recurring_application_charge", {})
                charge_id = str(charge_data.get("id"))
                status = charge_data.get("status")
                
                # Update subscription based on webhook
                result = await self.db.execute(
                    select(StoreSubscription).where(
                        and_(
                            StoreSubscription.store_id == store.id,
                            StoreSubscription.shopify_charge_id == charge_id
                        )
                    )
                )
                subscription = result.scalar_one_or_none()
                
                if subscription:
                    if status == "cancelled":
                        subscription.status = "cancelled"
                        subscription.cancelled_at = datetime.utcnow()
                    elif status == "expired":
                        subscription.status = "expired"
                        subscription.expires_at = datetime.utcnow()
                    elif status == "active":
                        subscription.status = "active"
                        subscription.activated_at = datetime.utcnow()
                    
                    # Log webhook event
                    event = BillingEvent(
                        store_id=store.id,
                        event_type=f"webhook_{webhook_topic}",
                        shopify_charge_id=charge_id,
                        status=status,
                        response_data=json.dumps(webhook_data)
                    )
                    self.db.add(event)
                    
                    await self.db.commit()
                    logger.info(f"Processed billing webhook {webhook_topic} for store {shop}")
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling billing webhook: {str(e)}")
            return False