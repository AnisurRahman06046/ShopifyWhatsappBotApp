from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.config import settings
from .whatsapp_repository import ShopifyStoreRepository
from pydantic import BaseModel
import httpx
import hmac
import hashlib
from urllib.parse import urlencode
import base64
import secrets

router = APIRouter(prefix="/shopify", tags=["shopify"])


class WhatsAppConfig(BaseModel):
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str
    whatsapp_business_account_id: str
    welcome_message: str = "👋 Welcome! Click 'Browse Products' to start shopping."


@router.post("/configure")
async def configure_whatsapp(
    config: WhatsAppConfig,
    shop: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Configure WhatsApp settings for a store"""
    
    repo = ShopifyStoreRepository(db)
    store = await repo.update_whatsapp_config(shop, config.dict())
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    return {"status": "success", "message": "WhatsApp configuration saved"}


@router.get("/admin")
async def admin_dashboard(shop: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    """Admin dashboard for managing WhatsApp bot"""
    
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    configured = all([
        store.whatsapp_token,
        store.whatsapp_phone_number_id,
        store.whatsapp_verify_token
    ])
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp Bot Dashboard - {store.shop_name}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .card {{
                background: white;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .card h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            .status {{
                display: inline-block;
                padding: 8px 15px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
            }}
            .status.active {{
                background: #d4edda;
                color: #155724;
            }}
            .status.inactive {{
                background: #f8d7da;
                color: #721c24;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background: #25D366;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: background 0.3s;
                margin-right: 10px;
                margin-top: 15px;
            }}
            .button:hover {{
                background: #128C7E;
            }}
            .button.secondary {{
                background: #6c757d;
            }}
            .button.secondary:hover {{
                background: #5a6268;
            }}
            .metric {{
                margin: 15px 0;
            }}
            .metric-value {{
                font-size: 32px;
                font-weight: bold;
                color: #333;
            }}
            .metric-label {{
                color: #666;
                font-size: 14px;
                margin-top: 5px;
            }}
            .widget-code {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                font-family: monospace;
                font-size: 12px;
                overflow-x: auto;
                margin-top: 15px;
            }}
            .instructions {{
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                border-radius: 5px;
                margin-top: 15px;
            }}
            .instructions h4 {{
                color: #1976d2;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📱 WhatsApp Bot Dashboard</h1>
                <p style="margin-top: 10px; opacity: 0.9;">{store.shop_name}</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>⚙️ Configuration Status</h3>
                    <span class="status {'active' if configured else 'inactive'}">
                        {'✅ Configured' if configured else '❌ Not Configured'}
                    </span>
                    <div style="margin-top: 15px;">
                        <strong>WhatsApp Status:</strong> 
                        <span class="status {'active' if store.whatsapp_enabled else 'inactive'}">
                            {'Active' if store.whatsapp_enabled else 'Inactive'}
                        </span>
                    </div>
                    <a href="/shopify/setup?shop={shop}" class="button">🔧 Configure</a>
                </div>
                
                <div class="card">
                    <h3>📊 Statistics</h3>
                    <div class="metric">
                        <div class="metric-value">0</div>
                        <div class="metric-label">Total Conversations</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">0</div>
                        <div class="metric-label">Orders via WhatsApp</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🚀 Quick Actions</h3>
                    <a href="#" onclick="testBot()" class="button">🧪 Test Bot</a>
                    <a href="/shopify/setup?shop={shop}" class="button secondary">⚙️ Settings</a>
                </div>
            </div>
            
            <div class="card">
                <h3>🛠️ Installation Guide</h3>
                
                <div class="instructions">
                    <h4>Step 1: Add WhatsApp Widget to Your Store</h4>
                    <p>Add this code to your theme's layout file (usually theme.liquid):</p>
                    <div class="widget-code">
&lt;!-- WhatsApp Chat Widget --&gt;
&lt;div id="whatsapp-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;"&gt;
    &lt;a href="https://wa.me/{store.whatsapp_phone_number_id or 'YOUR_PHONE_NUMBER'}?text=Hi" 
       target="_blank" 
       style="display: block; background: #25D366; border-radius: 50px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"&gt;
        &lt;svg width="30" height="30" fill="white" viewBox="0 0 24 24"&gt;
            &lt;path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.188"&gt;&lt;/path&gt;
        &lt;/svg&gt;
    &lt;/a&gt;
&lt;/div&gt;
                    </div>
                </div>
                
                {'<div class="instructions"><h4>Step 2: Configure Webhook in Meta Business</h4><p>1. Go to your Meta Business WhatsApp API settings</p><p>2. Add this webhook URL: <code>' + settings.REDIRECT_URI + '/whatsapp/webhook</code></p><p>3. Use this verify token: <code>' + (store.whatsapp_verify_token or 'NOT_SET') + '</code></p><p>4. Subscribe to: messages, messaging_postbacks</p></div>' if configured else ''}
            </div>
        </div>
        
        <script>
            function testBot() {{
                if ({str(configured).lower()}) {{
                    window.open('https://wa.me/{store.whatsapp_phone_number_id or ""}?text=Hi', '_blank');
                }} else {{
                    alert('Please configure WhatsApp settings first!');
                    window.location.href = '/shopify/setup?shop={shop}';
                }}
            }}
        </script>
    </body>
    </html>
    """)


@router.get("/install")
async def install_shopify_app(shop: str = Query(...)):
    """Initiate Shopify app installation"""
    
    if not shop.endswith('.myshopify.com'):
        raise HTTPException(status_code=400, detail="Invalid shop domain")
    
    # Generate nonce for security
    nonce = secrets.token_urlsafe(32)
    
    # Build install URL
    params = {
        "client_id": settings.SHOPIFY_API_KEY,
        "scope": settings.SHOPIFY_SCOPES,
        "redirect_uri": f"{settings.REDIRECT_URI}/shopify/callback",
        "state": nonce,
        "grant_options[]": "per-user"
    }
    
    install_url = f"https://{shop}/admin/oauth/authorize?" + urlencode(params)
    return RedirectResponse(url=install_url)


@router.get("/callback")
async def shopify_callback(
    code: str = Query(...),
    shop: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_async_db)
):
    """Handle Shopify OAuth callback"""
    
    # Exchange code for access token
    token_url = f"https://{shop}/admin/oauth/access_token"
    token_data = {
        "client_id": settings.SHOPIFY_API_KEY,
        "client_secret": settings.SHOPIFY_API_SECRET,
        "code": code
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        token_response = response.json()
        access_token = token_response["access_token"]
    
    # Get shop information
    shop_info_url = f"https://{shop}/admin/api/2024-01/shop.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(shop_info_url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get shop info")
        
        shop_data = response.json()["shop"]
    
    # Check if store already exists
    repo = ShopifyStoreRepository(db)
    existing_store = await repo.get_store_by_url(shop)
    
    if existing_store:
        # Update existing store
        existing_store.access_token = access_token
        existing_store.shop_name = shop_data["name"]
        await db.commit()
    else:
        # Create new store
        await repo.create_store(
            store_url=shop,
            access_token=access_token,
            shop_name=shop_data["name"]
        )
    
    # Redirect to setup page
    return RedirectResponse(url=f"/shopify/setup?shop={shop}")


@router.get("/setup")
async def setup_page(shop: str = Query(...), db: AsyncSession = Depends(get_async_db)):
    """Show WhatsApp configuration setup page"""
    
    repo = ShopifyStoreRepository(db)
    store = await repo.get_store_by_url(shop)
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found. Please install the app first.")
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp Bot Setup - {store.shop_name}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 100%;
                padding: 40px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }}
            .step {{
                background: #f8f9fa;
                border-left: 4px solid #25D366;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .step h3 {{
                color: #25D366;
                margin-bottom: 10px;
            }}
            .form-group {{
                margin: 20px 0;
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
                font-size: 14px;
            }}
            input, textarea {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e4e8;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }}
            input:focus, textarea:focus {{
                outline: none;
                border-color: #25D366;
            }}
            .help-text {{
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }}
            button {{
                background: #25D366;
                color: white;
                padding: 14px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s;
                width: 100%;
                margin-top: 20px;
            }}
            button:hover {{
                background: #128C7E;
            }}
            .alert {{
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .alert-info {{
                background: #e3f2fd;
                color: #1976d2;
                border-left: 4px solid #1976d2;
            }}
            .alert-success {{
                background: #e8f5e9;
                color: #2e7d32;
                display: none;
            }}
            .link {{
                color: #25D366;
                text-decoration: none;
                font-weight: 600;
            }}
            .link:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Setup WhatsApp Bot</h1>
            <p class="subtitle">for {store.shop_name}</p>
            
            <div class="alert alert-info">
                ℹ️ To use WhatsApp Bot, you need a Meta Business account with WhatsApp Business API access.
            </div>
            
            <div class="step">
                <h3>Step 1: Meta Business Setup</h3>
                <p>1. Go to <a href="https://business.facebook.com" target="_blank" class="link">Meta Business</a></p>
                <p>2. Create or select your WhatsApp Business App</p>
                <p>3. Get your credentials from the WhatsApp API Settings</p>
            </div>
            
            <form id="whatsapp-config-form">
                <input type="hidden" id="shop" value="{shop}">
                
                <div class="form-group">
                    <label for="whatsapp_token">WhatsApp Access Token *</label>
                    <input type="text" id="whatsapp_token" required 
                           placeholder="EAAxxxxx..." 
                           value="{store.whatsapp_token or ''}">
                    <div class="help-text">Found in: WhatsApp > API Setup > Temporary access token</div>
                </div>
                
                <div class="form-group">
                    <label for="whatsapp_phone_number_id">Phone Number ID *</label>
                    <input type="text" id="whatsapp_phone_number_id" required 
                           placeholder="1234567890..." 
                           value="{store.whatsapp_phone_number_id or ''}">
                    <div class="help-text">Found in: WhatsApp > API Setup > Phone numbers</div>
                </div>
                
                <div class="form-group">
                    <label for="whatsapp_business_account_id">WhatsApp Business Account ID *</label>
                    <input type="text" id="whatsapp_business_account_id" required 
                           placeholder="1234567890..." 
                           value="{store.whatsapp_business_account_id or ''}">
                    <div class="help-text">Found in: WhatsApp > API Setup > WhatsApp Business Account ID</div>
                </div>
                
                <div class="form-group">
                    <label for="whatsapp_verify_token">Webhook Verify Token *</label>
                    <input type="text" id="whatsapp_verify_token" required 
                           placeholder="my_verify_token_123" 
                           value="{store.whatsapp_verify_token or secrets.token_urlsafe(16)}">
                    <div class="help-text">Create your own secure token for webhook verification</div>
                </div>
                
                <div class="form-group">
                    <label for="welcome_message">Welcome Message</label>
                    <textarea id="welcome_message" rows="3" 
                              placeholder="Hi! Welcome to our store...">{store.welcome_message}</textarea>
                    <div class="help-text">Message sent when customer starts a conversation</div>
                </div>
                
                <button type="submit">💾 Save Configuration</button>
            </form>
            
            <div class="alert alert-success" id="success-message">
                ✅ Configuration saved! Now configure your webhook in Meta Business.
            </div>
            
            <div class="step" style="margin-top: 30px; display: none;" id="webhook-info">
                <h3>Step 2: Configure Webhook</h3>
                <p>Add this webhook URL in your WhatsApp API Configuration:</p>
                <p><strong>Webhook URL:</strong> <code>{settings.REDIRECT_URI}/whatsapp/webhook</code></p>
                <p><strong>Verify Token:</strong> <code id="verify-token-display"></code></p>
                <p><strong>Subscribe to:</strong> messages, messaging_postbacks</p>
            </div>
        </div>
        
        <script>
            document.getElementById('whatsapp-config-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const data = {{
                    whatsapp_token: document.getElementById('whatsapp_token').value,
                    whatsapp_phone_number_id: document.getElementById('whatsapp_phone_number_id').value,
                    whatsapp_business_account_id: document.getElementById('whatsapp_business_account_id').value,
                    whatsapp_verify_token: document.getElementById('whatsapp_verify_token').value,
                    welcome_message: document.getElementById('welcome_message').value
                }};
                
                const shop = document.getElementById('shop').value;
                
                try {{
                    const response = await fetch(`/shopify/configure?shop=${{shop}}`, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    
                    if (response.ok) {{
                        document.getElementById('success-message').style.display = 'block';
                        document.getElementById('webhook-info').style.display = 'block';
                        document.getElementById('verify-token-display').textContent = data.whatsapp_verify_token;
                        
                        setTimeout(() => {{
                            window.location.href = `/shopify/admin?shop=${{shop}}`;
                        }}, 3000);
                    }} else {{
                        alert('Error saving configuration. Please try again.');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }});
        </script>
    </body>
    </html>
    """)