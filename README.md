# 📱 WhatsApp Shopify Bot - Developer Documentation

A complete WhatsApp Shopping Bot for Shopify stores that allows customers to browse products, manage cart, and checkout directly through WhatsApp conversations.

## 🎯 Overview

This application enables Shopify store owners to install a WhatsApp bot on their store, allowing customers to:
- Browse products via WhatsApp
- Add items to cart
- Complete purchases through Shopify checkout
- Get personalized shopping assistance

## 🏗️ Architecture

### **Tech Stack**
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy (Async)
- **Cache**: Redis
- **APIs**: WhatsApp Business API, Shopify Admin API
- **Deployment**: Render/Heroku/Railway

### **Core Components**
```
app/
├── core/
│   ├── config.py          # Environment configuration
│   └── database.py        # Database setup
└── modules/
    ├── botConfig/          # App configuration
    └── whatsapp/           # WhatsApp bot functionality
        ├── whatsapp_models.py      # Database models
        ├── whatsapp_repository.py  # Data access layer
        ├── whatsapp_service.py     # WhatsApp & Shopify APIs
        ├── shopify_auth.py         # Shopify OAuth & Admin
        ├── webhook_handler.py      # WhatsApp webhook processing
        └── message_processor.py    # Bot conversation logic
```

## 🚀 Quick Start

### **Prerequisites**
1. **Shopify Partners Account** - [partners.shopify.com](https://partners.shopify.com)
2. **Meta Business Account** - [business.facebook.com](https://business.facebook.com)
3. **PostgreSQL Database**
4. **Redis Instance**
5. **Python 3.11+**

### **1. Clone & Setup**
```bash
git clone <your-repo>
cd wpBot
pip install -r requirements.txt
```

### **2. Environment Configuration**
Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/whatsapp_shopify_bot

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Shopify App (from Partners Dashboard)
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
SHOPIFY_SCOPES=read_products,read_orders,write_orders,read_customers

# Your App URL
REDIRECT_URI=https://your-app-domain.com

# Security
SECRET_KEY=your-super-secure-secret-key
WEBHOOK_SECRET=your-webhook-secret

# App Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info
```

### **3. Database Setup**
```bash
# Create database
createdb whatsapp_shopify_bot

# Run migrations
alembic upgrade head
```

### **4. Run Development Server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Shopify App Configuration

### **1. Create Shopify App**
1. Go to [Shopify Partners](https://partners.shopify.com)
2. Create new app
3. Configure app settings:

**App URLs:**
- App URL: `https://your-app.com`
- Allowed redirection URLs: `https://your-app.com/shopify/callback`
- App setup URL: `https://your-app.com/shopify/setup`

**Permissions:**
- `read_products` - Browse store products
- `read_orders` - View order history  
- `write_orders` - Create checkout sessions
- `read_customers` - Customer information

### **2. OAuth Flow**
```python
# Installation URL format:
https://your-app.com/shopify/install?shop=store.myshopify.com

# OAuth callback:
https://your-app.com/shopify/callback?code=xyz&shop=store.myshopify.com
```

## 📱 WhatsApp Business API Setup

### **1. Meta Business Manager Setup**
1. Create WhatsApp Business App
2. Get Phone Number ID
3. Generate Access Token
4. Configure webhook

### **2. Store-Specific Configuration**
Each store owner provides their own Meta Business credentials:
- **Access Token**: `EAAxxxxx...`
- **Phone Number ID**: `1234567890`
- **Business Account ID**: `9876543210`
- **Verify Token**: Custom security token

### **3. Webhook Configuration**
- **URL**: `https://your-app.com/whatsapp/webhook`
- **Verify Token**: Store-specific token
- **Subscriptions**: `messages`, `messaging_postbacks`

## 💾 Database Schema

### **ShopifyStore Table**
```sql
CREATE TABLE shopify_stores (
    id UUID PRIMARY KEY,
    store_url VARCHAR NOT NULL UNIQUE,
    access_token VARCHAR NOT NULL,
    shop_name VARCHAR NOT NULL,
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    whatsapp_token VARCHAR,
    whatsapp_phone_number_id VARCHAR,
    whatsapp_verify_token VARCHAR,
    whatsapp_business_account_id VARCHAR,
    welcome_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **WhatsAppSession Table**
```sql
CREATE TABLE whatsapp_sessions (
    id UUID PRIMARY KEY,
    phone_number VARCHAR NOT NULL UNIQUE,
    shopify_store_url VARCHAR NOT NULL,
    session_state VARCHAR DEFAULT 'browsing',
    cart_data TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔄 Message Flow Architecture

### **1. Incoming Message Processing**
```python
WhatsApp → /whatsapp/webhook → 
    Extract phone_number_id → 
    Find Store in DB → 
    Initialize Services → 
    Process Message → 
    Send Response
```

### **2. Store Identification**
```python
# webhook_handler.py
metadata = webhook_data.get("metadata", {})
phone_number_id = metadata.get("phone_number_id")

# Find store by WhatsApp phone number
store = await store_repo.get_store_by_phone_number(phone_number_id)
```

### **3. Service Initialization**
```python
# Use store-specific credentials
whatsapp_service = WhatsAppService(store)  # store.whatsapp_token
shopify_service = ShopifyService(store.store_url, store.access_token)
```

## 🛍️ Shopping Flow Implementation

### **1. Product Browsing**
```python
# message_processor.py
async def show_products(self, from_number: str):
    products = await self.shopify.get_products(limit=10)
    
    sections = [{
        "title": "Available Products",
        "rows": [
            {
                "id": f"product_{product['id']}",
                "title": product["title"][:24],
                "description": f"${product['price']}"
            }
            for product in products
        ]
    }]
    
    await self.whatsapp.send_list_message(
        to=from_number,
        text="📦 Here are our available products:",
        button_text="View Products",
        sections=sections
    )
```

### **2. Cart Management**
```python
async def add_to_cart(self, from_number: str, product_id: str, session):
    # Get current cart
    cart = await self.repo.get_cart(from_number)
    
    # Add product
    cart_item = {
        "product_id": product_id,
        "variant_id": variant_id,
        "title": product["title"],
        "price": product["price"],
        "quantity": 1
    }
    cart.append(cart_item)
    
    # Save to database
    await self.repo.update_cart(from_number, cart)
```

### **3. Checkout Process**
```python
async def start_checkout(self, from_number: str, session):
    cart = await self.repo.get_cart(from_number)
    
    # Create Shopify checkout
    line_items = [
        {
            "variant_id": item["variant_id"],
            "quantity": item["quantity"]
        }
        for item in cart
    ]
    
    checkout_url = await self.shopify.create_checkout(line_items)
    
    await self.whatsapp.send_message(
        to=from_number,
        message=f"🎉 Complete your purchase: {checkout_url}"
    )
```

## 🔐 Security Considerations

### **1. Webhook Verification**
```python
def verify_webhook(data: bytes, signature: str) -> bool:
    expected_signature = base64.b64encode(
        hmac.new(
            WEBHOOK_SECRET.encode(),
            data,
            digestmod=hashlib.sha256
        ).digest()
    ).decode()
    
    return hmac.compare_digest(signature, expected_signature)
```

### **2. Environment Variables**
- Never commit credentials to version control
- Use environment-specific `.env` files
- Generate strong random keys for production

### **3. Rate Limiting**
Implement rate limiting for API endpoints to prevent abuse:
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/whatsapp/webhook")
@limiter.limit("100/minute")
async def webhook_handler():
    # Processing logic
```

## 🚀 Deployment Guide

### **Render Deployment**
1. Connect GitHub repository
2. Set environment variables
3. Configure build settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### **Environment Variables for Production**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIRECT_URI=https://your-app.onrender.com
SHOPIFY_API_KEY=prod_api_key
SHOPIFY_API_SECRET=prod_api_secret
ENVIRONMENT=production
DEBUG=false
```

## 📊 Monitoring & Analytics

### **1. Logging**
```python
import logging
logger = logging.getLogger(__name__)

# Log important events
logger.info(f"New conversation started: {phone_number}")
logger.info(f"Product added to cart: {product_id}")
logger.info(f"Checkout completed: {checkout_url}")
```

### **2. Error Handling**
```python
try:
    await process_message()
except Exception as e:
    logger.error(f"Error processing webhook: {str(e)}")
    # Send error response or retry logic
```

## 🧪 Testing

### **1. Unit Tests**
```python
# test_message_processor.py
import pytest
from app.modules.whatsapp.message_processor import MessageProcessor

@pytest.mark.asyncio
async def test_add_to_cart():
    processor = MessageProcessor(mock_services...)
    result = await processor.add_to_cart("1234567890", "product_123", session)
    assert result is not None
```

### **2. Integration Tests**
```python
# Test Shopify API integration
@pytest.mark.asyncio
async def test_shopify_products():
    service = ShopifyService("test-store.myshopify.com", "access_token")
    products = await service.get_products()
    assert len(products) > 0
```

## 🔧 Troubleshooting

### **Common Issues**

**1. "Store not found" errors**
- Check if `whatsapp_phone_number_id` matches between webhook and database
- Verify store configuration is complete

**2. Shopify API errors** 
- Check access token validity
- Verify API permissions/scopes
- Check rate limits

**3. WhatsApp webhook not receiving messages**
- Verify webhook URL is accessible
- Check verify token matches
- Ensure HTTPS certificate is valid

### **Debug Mode**
Enable debug logging to troubleshoot:
```bash
DEBUG=true
LOG_LEVEL=debug
```

## 📈 Scaling Considerations

### **1. Database Optimization**
- Add indexes on frequently queried fields
- Implement connection pooling
- Consider read replicas for high traffic

### **2. Caching Strategy**
- Cache product data in Redis
- Cache frequently accessed store configurations
- Implement session caching

### **3. Queue System**
For high-volume stores, implement message queuing:
```python
# Use Celery or similar
@celery_app.task
async def process_webhook_message(webhook_data):
    await handle_messages(webhook_data)
```

## 🤝 Contributing

### **Development Workflow**
1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### **Code Standards**
- Follow PEP 8
- Add type hints
- Include docstrings
- Write tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/AnisurRahman06046/ShopifyWhatsappBotApp.git)
- **API Reference**: `/docs` endpoint (FastAPI auto-generated)

---

*This documentation covers the complete development, deployment, and maintenance of the WhatsApp Shopify Bot. For questions or contributions, please refer to the support channels above.*