# app/modules/billing/billing_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import get_async_db
from app.core.config import settings
from app.modules.whatsapp.whatsapp_repository import ShopifyStoreRepository
from .billing_service import BillingService
from .billing_models import BillingPlan, StoreSubscription
from datetime import datetime
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans")
async def get_billing_plans(db: AsyncSession = Depends(get_async_db)):
    """Get all available billing plans"""
    
    service = BillingService(db)
    plans = await service.get_or_create_default_plans()
    
    return {
        "plans": [
            {
                "id": str(plan.id),
                "name": plan.name,
                "price": plan.price,
                "interval": plan.interval,
                "trial_days": plan.trial_days,
                "messages_limit": plan.messages_limit,
                "features": json.loads(plan.features) if plan.features else {},
                "terms": plan.terms
            }
            for plan in plans
        ]
    }


@router.get("/select-plan")
async def select_plan_page(
    shop: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Display plan selection page"""
    
    # Get store
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Get plans
    service = BillingService(db)
    plans = await service.get_or_create_default_plans()
    
    # Get current subscription
    subscription = await service.get_store_subscription(store.id)
    current_plan_name = subscription.plan.name if subscription and subscription.plan else "None"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Select Your Plan - WhatsApp Shopping Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }}
            h1 {{
                font-size: 36px;
                margin-bottom: 10px;
            }}
            .subtitle {{
                font-size: 18px;
                opacity: 0.9;
            }}
            .current-plan {{
                background: rgba(255, 255, 255, 0.2);
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                display: inline-block;
                margin-top: 10px;
            }}
            .plans-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 30px;
                margin-bottom: 30px;
            }}
            .plan-card {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                position: relative;
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
            }}
            .plan-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }}
            .plan-card.recommended {{
                border: 3px solid #25D366;
            }}
            .recommended-badge {{
                position: absolute;
                top: -15px;
                left: 50%;
                transform: translateX(-50%);
                background: #25D366;
                color: white;
                padding: 5px 20px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }}
            .plan-name {{
                font-size: 24px;
                font-weight: 700;
                color: #333;
                margin-bottom: 10px;
            }}
            .plan-price {{
                font-size: 48px;
                font-weight: 700;
                color: #25D366;
                margin: 20px 0;
            }}
            .plan-price .currency {{
                font-size: 24px;
                vertical-align: top;
            }}
            .plan-price .period {{
                font-size: 16px;
                color: #666;
                font-weight: 400;
            }}
            .plan-trial {{
                background: #e3f2fd;
                color: #1976d2;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 14px;
                display: inline-block;
                margin-bottom: 20px;
            }}
            .plan-features {{
                list-style: none;
                margin: 30px 0;
                text-align: left;
            }}
            .plan-features li {{
                padding: 10px 0;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .plan-features li:last-child {{
                border-bottom: none;
            }}
            .check-icon {{
                color: #25D366;
                font-weight: bold;
            }}
            .select-button {{
                background: #25D366;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: background 0.3s;
            }}
            .select-button:hover {{
                background: #128C7E;
            }}
            .select-button.current {{
                background: #6c757d;
                cursor: not-allowed;
            }}
            .loading {{
                display: none;
                text-align: center;
                color: white;
                font-size: 18px;
                margin-top: 20px;
            }}
            .error-message {{
                display: none;
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📱 Choose Your Plan</h1>
                <p class="subtitle">Select the perfect plan for your WhatsApp Shopping Bot</p>
                <div class="current-plan">Current Plan: {current_plan_name}</div>
            </div>
            
            <div class="plans-grid">
    """
    
    # Add each plan
    for i, plan in enumerate(plans):
        features = json.loads(plan.features) if plan.features else {}
        is_recommended = plan.name == "Starter"
        is_current = plan.name == current_plan_name
        
        # Format price properly
        if plan.price == int(plan.price):
            price_display = f"{int(plan.price)}"
        else:
            price_display = f"{plan.price:.2f}"
        
        # Feature display mapping
        feature_display = {
            "basic_chat": "✅ WhatsApp Chat Integration",
            "product_browsing": "✅ Product Browsing",
            "cart_management": "✅ Cart Management",
            "checkout": "✅ Shopify Checkout",
            "automated_responses": "✅ Automated Responses",
            "analytics": "✅ Basic Analytics",
            "advanced_analytics": "✅ Advanced Analytics",
            "custom_branding": "✅ Custom Branding",
            "priority_support": "✅ Priority Support",
            "api_access": "✅ API Access",
            "white_label": "✅ White Label Option",
            "custom_integrations": "✅ Custom Integrations",
            "sla": "✅ SLA Guarantee"
        }
        
        html_content += f"""
            <div class="plan-card {'recommended' if is_recommended else ''}">
                {'<div class="recommended-badge">RECOMMENDED</div>' if is_recommended else ''}
                <div class="plan-name">{plan.name}</div>
                <div class="plan-price">
                    <span class="currency">$</span>{price_display}
                    <span class="period">/month</span>
                </div>
                {f'<div class="plan-trial">{plan.trial_days} day free trial</div>' if plan.trial_days > 0 and plan.price > 0 else ''}
                <ul class="plan-features">
                    <li><span class="check-icon">✓</span> {plan.messages_limit:,} messages/month</li>
        """
        
        # Add features
        for feature_key, feature_value in features.items():
            if feature_value and feature_key in feature_display:
                html_content += f'<li><span class="check-icon">✓</span> {feature_display[feature_key].replace("✅ ", "")}</li>'
        
        button_text = "Current Plan" if is_current else "Select Plan"
        button_class = "current" if is_current else ""
        
        html_content += f"""
                </ul>
                <button class="select-button {button_class}" 
                        onclick="selectPlan('{plan.id}', '{plan.name}')"
                        {'disabled' if is_current else ''}>
                    {button_text}
                </button>
            </div>
        """
    
    html_content += """
            </div>
            
            <div class="loading" id="loading">
                Processing your selection...
            </div>
            
            <div class="error-message" id="error-message"></div>
        </div>
        
        <script>
            async function selectPlan(planId, planName) {
                if (confirm(`Are you sure you want to select the ${planName} plan?`)) {
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('error-message').style.display = 'none';
                    
                    try {
                        const response = await fetch(`/billing/create-charge?shop=${encodeURIComponent('""" + shop + """')}&plan_id=${planId}`, {
                            method: 'POST'
                        });
                        
                        const data = await response.json();
                        
                        if (data.confirmation_url) {
                            // Redirect to Shopify confirmation page for paid plans
                            window.top.location.href = data.confirmation_url;
                        } else if (data.redirect_url) {
                            // Redirect to app dashboard for free plan
                            window.top.location.href = data.redirect_url;
                        } else if (data.status === 'success') {
                            // Fallback for successful free plan activation
                            window.top.location.href = `/shopify/setup?shop=${encodeURIComponent('""" + shop + """')}`;
                        } else {
                            throw new Error(data.detail || data.message || 'Failed to create charge');
                        }
                    } catch (error) {
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('error-message').style.display = 'block';
                        document.getElementById('error-message').textContent = 'Error: ' + error.message;
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/create-charge")
async def create_charge(
    shop: str = Query(...),
    plan_id: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a recurring charge for the selected plan"""
    
    # Get store
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store or not store.access_token:
        raise HTTPException(status_code=404, detail="Store not found or not authenticated")
    
    # Get plan
    result = await db.execute(
        select(BillingPlan).where(BillingPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Skip billing for free plan
    if plan.price == 0:
        try:
            logger.info(f"Activating free plan for shop: {shop}")
            # Create free subscription directly
            service = BillingService(db)
            
            # Cancel any existing subscription
            await service.cancel_subscription(shop, store.access_token)
            
            # Create new free subscription
            subscription = StoreSubscription(
                store_id=store.id,
                plan_id=plan.id,
                status="active",
                activated_at=datetime.utcnow()
            )
            db.add(subscription)
            await db.commit()
            
            logger.info(f"Free plan activated successfully for shop: {shop}")
            return {
                "status": "success",
                "message": "Free plan activated",
                "redirect_url": f"/shopify/setup?shop={shop}"
            }
        except Exception as e:
            logger.error(f"Error activating free plan for {shop}: {str(e)}")
            import traceback
            logger.error(f"Free plan traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to activate free plan: {str(e)}")
    
    # Create recurring charge
    service = BillingService(db)
    return_url = f"{settings.REDIRECT_URI}/billing/confirm?shop={shop}"
    
    try:
        logger.info(f"Creating charge for shop: {shop}, plan: {plan.name}, price: {plan.price}")
        charge_result = await service.create_recurring_charge(
            shop=shop,
            access_token=store.access_token,
            plan=plan,
            return_url=return_url
        )
        
        return {
            "status": "success",
            "charge_id": charge_result["charge_id"],
            "confirmation_url": charge_result["confirmation_url"]
        }
        
    except Exception as e:
        logger.error(f"Error creating charge for {shop}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create charge: {str(e)}")


@router.get("/confirm")
async def confirm_charge(
    shop: str = Query(...),
    charge_id: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Handle charge confirmation callback from Shopify"""
    
    # Get store
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store or not store.access_token:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Activate the charge
    service = BillingService(db)
    success = await service.activate_charge(shop, charge_id, store.access_token)
    
    if success:
        # Redirect to admin dashboard
        return RedirectResponse(url=f"/shopify/setup?shop={shop}&billing=success")
    else:
        # Redirect with error
        return RedirectResponse(url=f"/shopify/admin?shop={shop}&billing=failed")


@router.post("/cancel")
async def cancel_subscription(
    shop: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel the current subscription"""
    
    # Get store
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store or not store.access_token:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Cancel subscription
    service = BillingService(db)
    success = await service.cancel_subscription(shop, store.access_token)
    
    if success:
        return {"status": "success", "message": "Subscription cancelled"}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/usage")
async def get_usage(
    shop: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current usage statistics for the store"""
    
    # Get store
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Get usage information
    service = BillingService(db)
    usage = await service.check_usage_limit(store.id)
    
    return usage


@router.post("/webhooks/recurring_application_charge/update")
async def handle_charge_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Handle recurring charge update webhooks from Shopify"""
    
    try:
        # Get webhook data
        webhook_data = await request.json()
        shop = request.headers.get("X-Shopify-Shop-Domain")
        
        if not shop:
            raise HTTPException(status_code=400, detail="Missing shop domain")
        
        # Process webhook
        service = BillingService(db)
        success = await service.handle_billing_webhook(webhook_data, shop)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process webhook")
            
    except Exception as e:
        logger.error(f"Error processing billing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))