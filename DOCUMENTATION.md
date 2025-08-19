# WhatsApp Shopping Bot for Shopify - Complete Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)  
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Message Flow](#message-flow)
9. [Shopify Integration](#shopify-integration)
10. [WhatsApp Business API](#whatsapp-business-api)
11. [GDPR Compliance](#gdpr-compliance)
12. [Security](#security)
13. [Troubleshooting](#troubleshooting)
14. [Deployment](#deployment)
15. [Testing](#testing)
16. [Performance & Scaling](#performance--scaling)

---

## Overview

The WhatsApp Shopping Bot is a Shopify application that enables customers to browse products, manage shopping carts, and complete purchases directly through WhatsApp conversations. It bridges the gap between social commerce and traditional e-commerce by leveraging WhatsApp's 2+ billion user base.

### Key Benefits

- **Higher Engagement**: 85% higher engagement rates compared to email
- **Instant Communication**: Real-time product browsing and support
- **Cart Persistence**: Maintain shopping sessions across conversations
- **Mobile-First**: Optimized for mobile shopping experience
- **Global Reach**: Support for international customers via WhatsApp

---

## Features

### 🛍️ Shopping Experience

- **Product Catalog Browsing**: Browse entire Shopify inventory via WhatsApp
- **Smart Search**: Find products by name, category, or description
- **Quantity Management**: Increase/decrease product quantities with buttons
- **Cart Management**: Add, remove, and view cart items
- **Secure Checkout**: Generate secure Shopify checkout links
- **Order Tracking**: Real-time order status updates

### 🤖 Bot Intelligence

- **Natural Language Processing**: Understand customer queries
- **Session Management**: Maintain conversation context
- **Personalized Responses**: Customizable welcome and automated messages
- **Multi-language Support**: Configure for different markets
- **Fallback Handling**: Graceful error handling and recovery

### 📊 Business Features

- **Analytics Dashboard**: Track conversations and conversions
- **Inventory Sync**: Real-time product and stock updates
- **Customer Insights**: WhatsApp engagement metrics
- **GDPR Compliance**: Complete data protection compliance
- **Webhook Integration**: Real-time event processing

---

## Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   FastAPI        │    │   Shopify       │
│   Business API  │◄──►│   Application    │◄──►│   Store API     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   PostgreSQL     │
                       │   Database       │
                       └──────────────────┘
```

### Technology Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Message Queue**: Redis (optional)
- **Authentication**: OAuth 2.0 (Shopify)
- **API Integration**: 
  - Shopify Admin API v2024-01
  - WhatsApp Business API
- **Deployment**: Docker, AWS/Heroku compatible

### Project Structure

```
ShopifyWhatsappBotApp/
├── app/
│   ├── core/                    # Core application configuration
│   │   ├── config.py           # Environment configuration
│   │   ├── database.py         # Database connection
│   │   └── model_loader.py     # Model initialization
│   ├── modules/
│   │   ├── botConfig/          # Bot configuration module
│   │   │   ├── bot_models.py   # Bot data models
│   │   │   ├── bot_repository.py
│   │   │   └── bot_routes.py
│   │   └── whatsapp/           # WhatsApp integration
│   │       ├── whatsapp_models.py      # Data models
│   │       ├── whatsapp_repository.py  # Database operations
│   │       ├── whatsapp_service.py     # Business logic
│   │       ├── message_processor.py    # Message handling
│   │       ├── webhook_handler.py      # Webhook endpoints
│   │       └── shopify_auth.py         # Shopify integration
├── alembic/                    # Database migrations
├── static/                     # Static assets
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── shopify.app.toml           # Shopify app manifest
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Shopify Partner Account
- Meta Business Account with WhatsApp Business API access

### Local Development Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd ShopifyWhatsappBotApp
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database Setup**
```bash
# Create database
createdb whatsapp_shopify_bot

# Run migrations
alembic upgrade head
```

6. **Start Application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/whatsapp_shopify_bot

# Shopify Configuration
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SHOPIFY_SCOPES=read_products,read_orders,write_orders,write_draft_orders,read_customers,write_customers

# Application Settings
SECRET_KEY=your_secret_key
WEBHOOK_SECRET=your_webhook_secret
REDIRECT_URI=https://your-domain.com
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=info

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Configuration

### Shopify App Configuration

1. **Create Shopify App**
   - Go to [Shopify Partners](https://partners.shopify.com)
   - Create new app
   - Configure app URLs:
     - App URL: `https://your-domain.com/`
     - Allowed redirection URLs: `https://your-domain.com/shopify/callback`

2. **Set Required Scopes**
```
read_products,read_orders,write_orders,write_draft_orders,read_customers,write_customers
```

3. **Configure Webhooks**
```
App uninstalled: https://your-domain.com/shopify/webhooks/app/uninstalled
GDPR data request: https://your-domain.com/shopify/gdpr/customers/data_request  
GDPR data deletion: https://your-domain.com/shopify/gdpr/customers/redact
GDPR shop deletion: https://your-domain.com/shopify/gdpr/shop/redact
```

### WhatsApp Business API Setup

1. **Meta Business Account**
   - Create Meta Business account
   - Add WhatsApp Business app
   - Get Business Account ID

2. **Get API Credentials**
   - Access Token (temporary/permanent)
   - Phone Number ID
   - WhatsApp Business Account ID
   - Webhook verify token (create your own)

3. **Configure Webhook**
   - URL: `https://your-domain.com/whatsapp/webhook`
   - Verify Token: Your custom token
   - Subscribe to: `messages`, `messaging_postbacks`

---

## API Reference

### Shopify Integration Endpoints

#### GET /shopify/admin
Admin dashboard for store configuration.

**Parameters:**
- `shop` (query, required): Store domain

**Response:**
```html
HTML dashboard with configuration form
```

#### POST /shopify/configure  
Configure WhatsApp settings for a store.

**Parameters:**
- `shop` (query, required): Store domain

**Request Body:**
```json
{
  "whatsapp_token": "EAAxxxxx...",
  "whatsapp_phone_number_id": "1234567890",
  "whatsapp_business_account_id": "1234567890", 
  "whatsapp_verify_token": "verify_token_123",
  "welcome_message": "Welcome to our store!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "WhatsApp configuration saved"
}
```

### WhatsApp Webhook Endpoints

#### GET /whatsapp/webhook
Webhook verification endpoint.

**Parameters:**
- `hub.mode` (query): Webhook mode
- `hub.challenge` (query): Challenge string
- `hub.verify_token` (query): Verify token

#### POST /whatsapp/webhook
Process incoming WhatsApp messages.

**Request Body:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "business_account_id",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "messages": [{
          "from": "1234567890",
          "id": "message_id",
          "timestamp": "1234567890",
          "text": {"body": "Hello"},
          "type": "text"
        }]
      }
    }]
  }]
}
```

### GDPR Compliance Endpoints

#### POST /shopify/webhooks/app/uninstalled
Handle app uninstallation.

#### POST /shopify/gdpr/customers/data_request  
Handle customer data requests.

#### POST /shopify/gdpr/customers/redact
Handle customer data deletion.

#### POST /shopify/gdpr/shop/redact
Handle shop data deletion.

### Bot Configuration Endpoints

#### GET /bot-config
Get bot configuration for a store.

#### POST /bot-config  
Update bot configuration.

**Request Body:**
```json
{
  "store_url": "example.myshopify.com",
  "whatsapp_token": "token",
  "phone_number_id": "123456789",
  "verify_token": "verify_123"
}
```

---

## Database Schema

### WhatsApp Sessions Table

```sql
CREATE TABLE whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    shopify_store_url VARCHAR(255) NOT NULL,
    session_state VARCHAR(50) DEFAULT 'browsing',
    cart_data TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Shopify Stores Table

```sql
CREATE TABLE shopify_stores (
    id SERIAL PRIMARY KEY,
    store_url VARCHAR(255) UNIQUE NOT NULL,
    shop_name VARCHAR(255),
    access_token TEXT,
    -- WhatsApp Configuration
    whatsapp_token TEXT,
    whatsapp_phone_number_id VARCHAR(50),
    whatsapp_verify_token VARCHAR(100),
    whatsapp_business_account_id VARCHAR(50),
    welcome_message TEXT DEFAULT '👋 Welcome! Click ''Browse Products'' to start shopping.',
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Bot Configurations Table

```sql
CREATE TABLE bot_configurations (
    id SERIAL PRIMARY KEY,
    store_url VARCHAR(255) UNIQUE NOT NULL,
    whatsapp_token TEXT,
    phone_number_id VARCHAR(50),
    verify_token VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Message Flow

### Customer Interaction Flow

```
1. Customer sends message to WhatsApp
2. WhatsApp forwards to webhook
3. Message processor extracts content
4. Session manager gets/creates user session  
5. Business logic processes request
6. Response generated and sent via WhatsApp API
7. Session state updated in database
```

### Message Types & Responses

#### 1. Welcome Message
**Trigger:** First message from customer
**Response:** 
- Welcome message
- Browse Products button
- Help/Support options

#### 2. Product Browsing  
**Trigger:** "Browse Products", "Show me products"
**Response:**
- Product list with images
- Category buttons
- Search functionality

#### 3. Product Selection
**Trigger:** Product selection
**Response:**
- Product details
- Price and availability
- Quantity controls (➖ Less, ➕ More)
- Add to Cart button

#### 4. Cart Management
**Trigger:** "Add to cart", "View cart"
**Response:**
- Cart contents
- Item quantities
- Total price
- Checkout button

#### 5. Checkout Process
**Trigger:** "Checkout", "Buy now" 
**Response:**
- Secure checkout link
- Order confirmation
- Tracking information

### Button Interactions

#### Quantity Controls
```python
# Button ID format: qty_increase_{product_id}_{current_quantity}
"qty_increase_123_1"  # Increase quantity from 1 to 2
"qty_decrease_123_2"  # Decrease quantity from 2 to 1
```

#### Cart Actions
```python  
# Add to cart with quantity
"add_to_cart_{product_id}_{quantity}"
"add_to_cart_123_2"  # Add 2 items of product 123

# Cart management
"view_cart"          # Show cart contents
"clear_cart"         # Empty cart
"checkout"           # Proceed to checkout
```

---

## Shopify Integration

### Admin API Usage

#### Product Fetching
```python
async def get_products(self, store_url: str, limit: int = 10):
    """Fetch products from Shopify store"""
    
    store = await self.get_store_by_url(store_url)
    if not store:
        return []
    
    headers = {
        "X-Shopify-Access-Token": store.access_token,
        "Content-Type": "application/json"
    }
    
    url = f"https://{store_url}/admin/api/2024-01/products.json"
    params = {"limit": limit, "status": "active"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        
    if response.status_code == 200:
        return response.json().get("products", [])
    return []
```

#### Draft Order Creation
```python
async def create_draft_order(self, store_url: str, cart_items: List[Dict]):
    """Create draft order for checkout"""
    
    store = await self.get_store_by_url(store_url)
    line_items = []
    
    for item in cart_items:
        line_items.append({
            "variant_id": item["variant_id"],
            "quantity": item["quantity"]
        })
    
    draft_order_data = {
        "draft_order": {
            "line_items": line_items,
            "use_customer_default_address": True
        }
    }
    
    headers = {
        "X-Shopify-Access-Token": store.access_token,
        "Content-Type": "application/json"
    }
    
    url = f"https://{store_url}/admin/api/2024-01/draft_orders.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, 
            headers=headers, 
            json=draft_order_data
        )
    
    if response.status_code == 201:
        draft_order = response.json()["draft_order"]
        return draft_order["invoice_url"]
    
    return None
```

### Cart Permalink Method (Primary)
```python
async def create_cart_permalink(self, store_url: str, cart_items: List[Dict]):
    """Create cart permalink URL (preferred method)"""
    
    # Build cart parameter string
    cart_params = []
    for item in cart_items:
        variant_id = item["variant_id"]
        quantity = item["quantity"]
        cart_params.append(f"{variant_id}:{quantity}")
    
    cart_string = ",".join(cart_params)
    checkout_url = f"https://{store_url}/cart/{cart_string}"
    
    return checkout_url
```

### Webhook Handling
```python
def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Shopify webhook signature"""
    
    if not signature:
        return False
    
    try:
        expected_signature = base64.b64encode(
            hmac.new(
                settings.SHOPIFY_WEBHOOK_SECRET.encode(),
                body,
                digestmod=hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        print(f"Webhook signature verification failed: {e}")
        return False
```

---

## WhatsApp Business API

### Message Sending

#### Text Messages
```python
async def send_text_message(self, to: str, text: str):
    """Send text message via WhatsApp Business API"""
    
    url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    headers = {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    
    return response.status_code == 200
```

#### Interactive Buttons  
```python
async def send_interactive_buttons(self, to: str, text: str, buttons: List[Dict]):
    """Send message with interactive buttons"""
    
    # Format buttons for WhatsApp API
    formatted_buttons = []
    for i, button in enumerate(buttons[:3]):  # Max 3 buttons
        formatted_buttons.append({
            "type": "reply",
            "reply": {
                "id": button["id"],
                "title": button["title"][:20]  # Max 20 chars
            }
        })
    
    payload = {
        "messaging_product": "whatsapp", 
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": formatted_buttons}
        }
    }
    
    url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {self.access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    
    return response.status_code == 200
```

#### Product Messages
```python
async def send_product_message(self, to: str, product: Dict, quantity: int = 1):
    """Send product information with interactive buttons"""
    
    price = float(product.get('price', 0))
    total_price = price * quantity
    
    text = f"""🛍️ {product['title']}
    
💰 Price: ${price:.2f}
📦 Quantity: {quantity}  
💵 Total: ${total_price:.2f}

{product.get('description', '')[:200]}"""

    buttons = [
        {"id": f"qty_decrease_{product['id']}_{quantity}", "title": "➖ Less"},
        {"id": f"qty_increase_{product['id']}_{quantity}", "title": "➕ More"},
        {"id": f"add_to_cart_{product['id']}_{quantity}", "title": f"🛒 Add {quantity} to Cart"}
    ]
    
    await self.send_interactive_buttons(to, text, buttons)
```

### Webhook Processing
```python
async def process_webhook(self, webhook_data: Dict):
    """Process incoming WhatsApp webhook"""
    
    entry = webhook_data.get("entry", [])
    if not entry:
        return
    
    changes = entry[0].get("changes", [])
    if not changes:
        return
        
    value = changes[0].get("value", {})
    messages = value.get("messages", [])
    
    for message in messages:
        await self.process_message(message)
```

---

## GDPR Compliance

### Data Collection

The application collects minimal data necessary for functionality:

1. **Customer Data**
   - WhatsApp phone numbers (for session continuity)
   - Shopping cart contents (temporary)
   - Session preferences

2. **Store Data** 
   - Shopify store URLs and names
   - WhatsApp API credentials
   - Configuration settings

### Data Processing Legal Basis

- **Contract Performance**: Processing necessary for WhatsApp shopping service
- **Legitimate Interests**: Service improvement and security monitoring  
- **Consent**: Explicit consent for additional features

### Data Retention Policies

- **Active Sessions**: Retained while app is installed
- **Customer Data**: Deleted 90 days after inactivity
- **Store Data**: Retained for compliance, credentials cleared on uninstall
- **Logs**: Retained for 30 days for debugging

### GDPR Endpoints Implementation

#### Customer Data Request
```python
async def get_customer_data(self, shop_domain: str, customer_phone: str = None):
    """Collect customer data for GDPR request"""
    
    sessions = []
    if customer_phone:
        result = await self.db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.phone_number == customer_phone
            )
        )
        sessions = result.scalars().all()
    
    return {
        "sessions": [
            {
                "phone_number": session.phone_number,
                "store": session.shopify_store_url,
                "session_state": session.session_state,
                "created_at": str(session.created_at),
                "cart_data": json.loads(session.cart_data) if session.cart_data else {}
            }
            for session in sessions
        ],
        "data_retention": "90 days after last activity",
        "contact": "privacy@ecommercexpart.com"
    }
```

#### Data Deletion  
```python
async def delete_customer_data(self, shop_domain: str, customer_phone: str = None):
    """Delete customer data for GDPR compliance"""
    
    deleted_count = 0
    
    if customer_phone:
        result = await self.db.execute(
            select(WhatsAppSession).where(
                WhatsAppSession.phone_number == customer_phone
            )
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            await self.db.delete(session)
            deleted_count += 1
        
        await self.db.commit()
    
    return deleted_count
```

---

## Security

### API Security

1. **Authentication**
   - OAuth 2.0 for Shopify integration
   - Bearer token authentication for WhatsApp API
   - Webhook signature verification

2. **Data Encryption**
   - TLS 1.3 for data in transit
   - Database encryption at rest
   - Secure credential storage

3. **Access Controls**
   - Store-specific data isolation
   - Role-based access control
   - API rate limiting

### Webhook Security

#### Signature Verification
```python
def verify_shopify_webhook(body: bytes, signature: str) -> bool:
    """Verify Shopify webhook authenticity"""
    
    expected_signature = base64.b64encode(
        hmac.new(
            SHOPIFY_WEBHOOK_SECRET.encode(),
            body,
            digestmod=hashlib.sha256
        ).digest()
    ).decode()
    
    return hmac.compare_digest(signature, expected_signature)

def verify_whatsapp_webhook(body: str, signature: str) -> bool:
    """Verify WhatsApp webhook authenticity"""
    
    expected_signature = hmac.new(
        WHATSAPP_WEBHOOK_SECRET.encode(),
        body.encode(),
        digestmod=hashlib.sha1
    ).hexdigest()
    
    return hmac.compare_digest(f"sha1={expected_signature}", signature)
```

### Data Protection

1. **Sensitive Data Handling**
   - API tokens encrypted in database
   - Customer data minimization
   - Secure session management

2. **Error Handling**
   - No sensitive data in logs
   - Graceful error responses
   - Security event monitoring

---

## Troubleshooting

### Common Issues

#### 1. WhatsApp Messages Not Sending

**Symptoms:**
- Bot receives messages but doesn't respond
- HTTP 400 errors in logs

**Solutions:**
```bash
# Check WhatsApp credentials
curl -X GET "https://graph.facebook.com/v18.0/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Verify phone number ID
curl -X GET "https://graph.facebook.com/v18.0/YOUR_BUSINESS_ACCOUNT_ID/phone_numbers" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Test message sending
curl -X POST "https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "TEST_PHONE_NUMBER", 
    "type": "text",
    "text": {"body": "Test message"}
  }'
```

#### 2. Shopify Products Not Loading

**Symptoms:**
- Empty product responses
- 401/403 errors from Shopify API

**Solutions:**
```python
# Check API permissions
async def test_shopify_connection(store_url: str, access_token: str):
    headers = {"X-Shopify-Access-Token": access_token}
    
    # Test shop access
    response = await client.get(
        f"https://{store_url}/admin/api/2024-01/shop.json",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Shop access failed: {response.status_code}")
        return False
        
    # Test products access  
    response = await client.get(
        f"https://{store_url}/admin/api/2024-01/products.json?limit=1",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Products access failed: {response.status_code}")
        return False
    
    return True
```

#### 3. Database Connection Issues

**Symptoms:**
- Application startup failures
- "Connection refused" errors

**Solutions:**
```bash
# Check database connectivity
psql postgresql://user:password@localhost/database_name -c "SELECT 1"

# Check connection pool
python -c "
import asyncpg
import asyncio

async def test_connection():
    conn = await asyncpg.connect('postgresql://user:pass@localhost/db')
    result = await conn.fetch('SELECT 1')
    await conn.close()
    print('Database connection successful')

asyncio.run(test_connection())
"
```

#### 4. Webhook Verification Failures

**Symptoms:**
- Webhook endpoints returning 401
- "Invalid signature" errors

**Solutions:**
```python
# Debug webhook signature
import hmac
import hashlib
import base64

def debug_webhook_signature(body: bytes, received_signature: str, secret: str):
    # Calculate expected signature
    expected = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    
    print(f"Received: {received_signature}")
    print(f"Expected: {expected}")
    print(f"Match: {hmac.compare_digest(received_signature, expected)}")
    
    return hmac.compare_digest(received_signature, expected)
```

### Debug Mode Setup

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add request/response logging
async def log_api_call(method: str, url: str, payload: dict = None):
    logger.debug(f"API Call: {method} {url}")
    if payload:
        logger.debug(f"Payload: {payload}")
```

### Performance Monitoring

```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## Deployment

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database migrations and start app
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/whatsapp_bot
      - SHOPIFY_API_KEY=${SHOPIFY_API_KEY}
      - SHOPIFY_API_SECRET=${SHOPIFY_API_SECRET}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=whatsapp_bot
      - POSTGRES_USER=postgres  
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Heroku Deployment

#### Procfile
```
web: alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### Deploy Commands
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Add Redis addon (optional)
heroku addons:create heroku-redis:mini

# Set environment variables
heroku config:set SHOPIFY_API_KEY=your_key
heroku config:set SHOPIFY_API_SECRET=your_secret
heroku config:set SECRET_KEY=$(openssl rand -base64 32)

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
```

### AWS Deployment

#### ECS Task Definition
```json
{
  "family": "whatsapp-shopify-bot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/whatsapp-bot:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "SHOPIFY_API_KEY", "value": "..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/whatsapp-shopify-bot",
          "awslogs-region": "us-west-2"
        }
      }
    }
  ]
}
```

---

## Testing

### Unit Tests

```python
# test_message_processor.py
import pytest
from app.modules.whatsapp.message_processor import MessageProcessor

@pytest.fixture
async def message_processor():
    return MessageProcessor(mock_db_session)

async def test_process_browse_products_message(message_processor):
    message = {
        "from": "1234567890",
        "text": {"body": "browse products"},
        "type": "text"
    }
    
    response = await message_processor.process_message(message, "store.myshopify.com")
    
    assert "products" in response.lower()
    assert len(response) > 0

async def test_add_to_cart_functionality(message_processor):
    # Test adding product to cart
    message = {
        "from": "1234567890", 
        "interactive": {
            "button_reply": {"id": "add_to_cart_123_2"}
        },
        "type": "interactive"
    }
    
    response = await message_processor.process_message(message, "store.myshopify.com")
    
    assert "added to cart" in response.lower()
```

### Integration Tests

```python
# test_shopify_integration.py
import pytest
import httpx
from unittest.mock import AsyncMock

async def test_shopify_product_fetching():
    # Mock Shopify API response
    mock_response = {
        "products": [
            {
                "id": 123,
                "title": "Test Product",
                "variants": [{"id": 456, "price": "29.99"}]
            }
        ]
    }
    
    with httpx_mock.HTTPXMock() as mock:
        mock.add_response(
            method="GET",
            url="https://test-store.myshopify.com/admin/api/2024-01/products.json",
            json=mock_response
        )
        
        products = await fetch_products("test-store.myshopify.com")
        assert len(products) == 1
        assert products[0]["title"] == "Test Product"

async def test_checkout_creation():
    # Test draft order creation
    cart_items = [{"variant_id": 456, "quantity": 2}]
    
    checkout_url = await create_checkout("test-store.myshopify.com", cart_items)
    
    assert checkout_url is not None
    assert "test-store.myshopify.com" in checkout_url
```

### End-to-End Tests

```python
# test_e2e_flow.py
async def test_complete_shopping_flow():
    """Test complete customer shopping journey"""
    
    # 1. Customer sends welcome message
    welcome_response = await send_whatsapp_message("Hello")
    assert "welcome" in welcome_response.lower()
    
    # 2. Customer browses products  
    browse_response = await send_whatsapp_message("Browse products")
    assert "products" in browse_response
    
    # 3. Customer adds product to cart
    add_response = await send_button_click("add_to_cart_123_1")
    assert "added to cart" in add_response.lower()
    
    # 4. Customer proceeds to checkout
    checkout_response = await send_button_click("checkout") 
    assert "checkout" in checkout_response.lower()
    assert "http" in checkout_response  # Contains checkout URL
```

### Load Testing

```python
# load_test.py
import asyncio
import aiohttp
import time

async def simulate_webhook_load():
    """Simulate high load on webhook endpoint"""
    
    concurrent_requests = 100
    total_requests = 1000
    
    async def send_request(session):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {"messages": [
                {"from": "1234567890", "text": {"body": "test"}, "type": "text"}
            ]}}]}]
        }
        
        async with session.post(
            "http://localhost:8000/whatsapp/webhook",
            json=payload
        ) as response:
            return response.status
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(total_requests):
            tasks.append(send_request(session))
            
            if len(tasks) >= concurrent_requests:
                responses = await asyncio.gather(*tasks)
                tasks = []
                
                success_rate = sum(1 for r in responses if r == 200) / len(responses)
                print(f"Success rate: {success_rate:.2%}")
    
    end_time = time.time()
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"RPS: {total_requests / (end_time - start_time):.2f}")

# Run load test
asyncio.run(simulate_webhook_load())
```

---

## Performance & Scaling

### Database Optimization

#### Indexing Strategy
```sql
-- Index for frequent lookups
CREATE INDEX idx_whatsapp_sessions_phone ON whatsapp_sessions(phone_number);
CREATE INDEX idx_whatsapp_sessions_store ON whatsapp_sessions(shopify_store_url);
CREATE INDEX idx_shopify_stores_url ON shopify_stores(store_url);

-- Composite index for session queries
CREATE INDEX idx_sessions_phone_store ON whatsapp_sessions(phone_number, shopify_store_url);

-- Index for cleanup queries
CREATE INDEX idx_sessions_updated_at ON whatsapp_sessions(updated_at);
```

#### Connection Pooling
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Caching Strategy

#### Redis Implementation
```python
import redis.asyncio as redis
import json

class CacheManager:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")
    
    async def cache_products(self, store_url: str, products: List[Dict]):
        """Cache products for 5 minutes"""
        key = f"products:{store_url}"
        await self.redis.setex(key, 300, json.dumps(products))
    
    async def get_cached_products(self, store_url: str):
        """Get cached products"""
        key = f"products:{store_url}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def cache_session(self, phone_number: str, session_data: Dict):
        """Cache session for quick access"""
        key = f"session:{phone_number}"
        await self.redis.setex(key, 1800, json.dumps(session_data))  # 30 min
```

### Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Initialize rate limiter
await FastAPILimiter.init(redis)

# Apply to webhook endpoints
@app.post("/whatsapp/webhook")
@limiter(RateLimiter(times=100, seconds=60))  # 100 requests per minute
async def whatsapp_webhook(request: Request):
    # ... webhook processing
```

### Monitoring & Metrics

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
MESSAGE_COUNTER = Counter('whatsapp_messages_total', 'Total WhatsApp messages', ['type', 'store'])
RESPONSE_TIME = Histogram('whatsapp_response_time_seconds', 'Response time for messages')
ERROR_COUNTER = Counter('whatsapp_errors_total', 'Total errors', ['error_type'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Usage in code
MESSAGE_COUNTER.labels(type="text", store=store_url).inc()

with RESPONSE_TIME.time():
    await process_message(message)
```

#### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        await db.execute(select(1))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        await redis.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
```

### Scaling Considerations

1. **Horizontal Scaling**
   - Stateless application design
   - Database session management
   - Load balancer configuration

2. **Database Scaling**
   - Read replicas for product queries
   - Connection pooling optimization
   - Query optimization

3. **Message Queue Integration**
   - Async message processing
   - Retry mechanisms
   - Dead letter queues

4. **CDN Integration**
   - Static asset delivery
   - API response caching
   - Geographic distribution

---

## Conclusion

This documentation provides comprehensive coverage of the WhatsApp Shopping Bot for Shopify. The system is designed to be scalable, secure, and compliant with all relevant regulations.

### Key Takeaways

- **Complete Integration**: Seamless connection between WhatsApp, Shopify, and your customers
- **User Experience**: Intuitive shopping flow with persistent cart management
- **Security**: Enterprise-grade security with GDPR compliance
- **Scalability**: Designed to handle growth from startup to enterprise
- **Maintainability**: Well-structured code with comprehensive testing

For additional support or questions, contact: support@ecommercexpart.com

---

**Last Updated**: August 19, 2025
**Version**: 1.0.0
**License**: Proprietary