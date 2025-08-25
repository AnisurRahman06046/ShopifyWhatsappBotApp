from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from .billing_service import BillingService
from app.modules.whatsapp.whatsapp_repository import ShopifyStoreRepository
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/usage/{shop_domain}")
async def get_usage_stats(
    shop_domain: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get message usage statistics for a store"""
    
    try:
        # Get store by domain
        store_repo = ShopifyStoreRepository(db)
        store = await store_repo.get_store_by_url(shop_domain)
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Get usage statistics
        billing_service = BillingService(db)
        usage_stats = await billing_service.check_usage_limit(store.id)
        subscription = await billing_service.get_store_subscription(store.id)
        
        return {
            "store_domain": shop_domain,
            "store_name": store.shop_name,
            "subscription": {
                "plan_name": subscription.plan.name if subscription and subscription.plan else "Free",
                "status": subscription.status if subscription else "active",
                "messages_limit": usage_stats.get("messages_limit", 100),
                "messages_used": usage_stats.get("messages_used", 0),
                "messages_remaining": usage_stats.get("messages_remaining", 100),
                "limit_reached": usage_stats.get("limit_reached", False),
                "reset_date": usage_stats.get("reset_date").isoformat() if usage_stats.get("reset_date") else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage")
async def usage_dashboard(db: AsyncSession = Depends(get_async_db)):
    """Admin dashboard showing usage across all stores"""
    
    try:
        store_repo = ShopifyStoreRepository(db)
        billing_service = BillingService(db)
        
        # Get all stores
        stores = await store_repo.get_all_stores()
        
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhatsApp Bot Usage Dashboard</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }
                .header { background: linear-gradient(135deg, #25D366, #128C7E); color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .store-card { background: white; border: 1px solid #e1e8ed; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .plan-free { border-left: 4px solid #gray; }
                .plan-basic { border-left: 4px solid #667eea; }
                .plan-premium { border-left: 4px solid #ff6b6b; }
                .usage-bar { background: #f0f0f0; height: 20px; border-radius: 10px; margin: 10px 0; overflow: hidden; }
                .usage-fill { height: 100%; background: linear-gradient(90deg, #25D366, #128C7E); transition: width 0.3s ease; }
                .usage-fill.warning { background: linear-gradient(90deg, #ffa500, #ff8c00); }
                .usage-fill.danger { background: linear-gradient(90deg, #ff6b6b, #ee5a52); }
                .metric { display: flex; justify-content: space-between; margin: 10px 0; }
                .status-active { color: #25D366; font-weight: bold; }
                .status-warning { color: #ffa500; font-weight: bold; }
                .status-limit { color: #ff6b6b; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 WhatsApp Bot Usage Dashboard</h1>
                <p>Monitor message usage across all stores</p>
            </div>
            <div class="stats-grid">
        """
        
        total_stores = 0
        stores_near_limit = 0
        stores_over_limit = 0
        
        for store in stores:
            total_stores += 1
            usage_stats = await billing_service.check_usage_limit(store.id)
            subscription = await billing_service.get_store_subscription(store.id)
            
            plan_name = subscription.plan.name if subscription and subscription.plan else "Free"
            messages_used = usage_stats.get("messages_used", 0)
            messages_limit = usage_stats.get("messages_limit", 100)
            limit_reached = usage_stats.get("limit_reached", False)
            usage_percent = (messages_used / messages_limit * 100) if messages_limit > 0 else 0
            
            if limit_reached:
                stores_over_limit += 1
                status_class = "status-limit"
                status_text = "LIMIT REACHED"
                usage_fill_class = "danger"
            elif usage_percent >= 80:
                stores_near_limit += 1
                status_class = "status-warning" 
                status_text = "NEAR LIMIT"
                usage_fill_class = "warning"
            else:
                status_class = "status-active"
                status_text = "ACTIVE"
                usage_fill_class = ""
            
            plan_class = f"plan-{plan_name.lower()}"
            
            dashboard_html += f"""
                <div class="store-card {plan_class}">
                    <h3>{store.shop_name}</h3>
                    <div class="metric">
                        <span>Domain:</span>
                        <span>{store.store_url}</span>
                    </div>
                    <div class="metric">
                        <span>Plan:</span>
                        <span><strong>{plan_name}</strong></span>
                    </div>
                    <div class="metric">
                        <span>Status:</span>
                        <span class="{status_class}">{status_text}</span>
                    </div>
                    <div class="metric">
                        <span>Messages:</span>
                        <span>{messages_used:,} / {messages_limit:,}</span>
                    </div>
                    <div class="usage-bar">
                        <div class="usage-fill {usage_fill_class}" style="width: {min(usage_percent, 100):.1f}%"></div>
                    </div>
                    <div class="metric">
                        <span>Usage:</span>
                        <span>{usage_percent:.1f}%</span>
                    </div>
                    <div class="metric">
                        <span>Remaining:</span>
                        <span>{usage_stats.get('messages_remaining', 0):,}</span>
                    </div>
                </div>
            """
        
        # Summary stats
        summary_html = f"""
        </div>
        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <h2>📈 Summary Statistics</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
                <div style="text-align: center; background: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #25D366;">{total_stores}</div>
                    <div>Total Stores</div>
                </div>
                <div style="text-align: center; background: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #ffa500;">{stores_near_limit}</div>
                    <div>Near Limit (80%+)</div>
                </div>
                <div style="text-align: center; background: white; padding: 20px; border-radius: 8px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #ff6b6b;">{stores_over_limit}</div>
                    <div>Over Limit</div>
                </div>
            </div>
        </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=dashboard_html + summary_html)
        
    except Exception as e:
        logger.error(f"Error generating usage dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-usage/{shop_domain}")
async def reset_usage_counter(
    shop_domain: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Reset message usage counter for a store (admin only)"""
    
    try:
        store_repo = ShopifyStoreRepository(db)
        store = await store_repo.get_store_by_url(shop_domain)
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        billing_service = BillingService(db)
        subscription = await billing_service.get_store_subscription(store.id)
        
        if subscription:
            subscription.messages_used = 0
            await db.commit()
            logger.info(f"Reset usage counter for store {shop_domain}")
            
            return {
                "success": True,
                "message": f"Usage counter reset for {shop_domain}",
                "new_usage": 0
            }
        else:
            raise HTTPException(status_code=404, detail="No subscription found for store")
            
    except Exception as e:
        logger.error(f"Error resetting usage counter: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))