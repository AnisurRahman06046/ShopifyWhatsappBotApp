# main.py
from fastapi import FastAPI
from app.modules.botConfig.bot_routes import router as bot_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="WhatsApp Shopify Bot",
    description="A WhatsApp bot for Shopify stores",
    version="1.0.0"
)

# Serve static HTML files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(bot_router)

# WhatsApp and Shopify routes
from app.modules.whatsapp.shopify_auth import router as shopify_router
from app.modules.whatsapp.webhook_handler import router as whatsapp_router

app.include_router(shopify_router)
app.include_router(whatsapp_router)

@app.get("/")
async def root():
    return {"message": "WhatsApp Shopify Bot API", "docs": "/docs"}
