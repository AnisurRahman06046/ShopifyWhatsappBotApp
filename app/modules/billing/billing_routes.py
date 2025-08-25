# app/modules/billing/billing_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="app/templates")


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
    request: Request,
    shop: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Display plan selection page using the new template"""
    
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
    
    # Use the new template instead of the old HTML
    return templates.TemplateResponse("select_plan.html", {
        "request": request,
        "shop": shop,
        "plans": plans,
        "current_plan": current_plan_name,
        "store_name": store.shop_name
    })


@router.post("/create-charge")
async def create_charge(
    shop: str = Query(...),
    plan_id: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a recurring charge for the selected plan"""
    
    try:
        # Get store
        repo = ShopifyStoreRepository(db)
        store = await repo.get_store_by_url(shop)
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Get plan
        result = await db.execute(
            select(BillingPlan).where(BillingPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Create billing service
        service = BillingService(db)
        
        # For free plan, just activate directly
        if plan.price == 0:
            await service.activate_free_plan(store, plan)
            return {"success": True, "redirect_url": f"/shopify/setup?shop={shop}"}
        
        # For paid plans, create Shopify charge
        charge_result = await service.create_recurring_charge(
            shop=shop,
            access_token=store.access_token,
            plan=plan,
            return_url=f"https://sc.ecommercexpart.com/billing/confirm-charge?shop={shop}"
        )
        
        return {
            "success": True,
            "confirmation_url": charge_result.get("confirmation_url"),
            "charge_id": charge_result.get("charge_id")
        }
        
    except Exception as e:
        logger.error(f"Error creating charge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/confirm-charge")
async def confirm_charge(
    shop: str = Query(...),
    charge_id: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Confirm and activate the charge after payment"""
    
    try:
        # Get store
        repo = ShopifyStoreRepository(db)
        store = await repo.get_store_by_url(shop)
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Activate charge
        service = BillingService(db)
        result = await service.activate_recurring_charge(
            shop=shop,
            access_token=store.access_token,
            charge_id=charge_id
        )
        
        if result.get("success"):
            # Redirect to app setup
            return RedirectResponse(url=f"/shopify/setup?shop={shop}")
        else:
            raise HTTPException(status_code=400, detail="Failed to activate charge")
            
    except Exception as e:
        logger.error(f"Error confirming charge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cancel-subscription")
async def cancel_subscription(
    shop: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel current subscription"""
    
    try:
        # Get store
        repo = ShopifyStoreRepository(db)
        store = await repo.get_store_by_url(shop)
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Cancel subscription
        service = BillingService(db)
        result = await service.cancel_subscription(store.id)
        
        return {"success": result, "message": "Subscription cancelled"}
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))