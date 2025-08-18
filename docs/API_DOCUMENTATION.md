# 📡 API Documentation

Complete API reference for the WhatsApp Shopify Bot, including all endpoints, request/response schemas, and usage examples.

## 🌐 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-app.onrender.com`

## 🔐 Authentication

The API uses different authentication methods depending on the endpoint type:

- **Shopify OAuth**: For store authentication
- **WhatsApp Webhooks**: Signature verification
- **Internal APIs**: No authentication (protected by environment)

---

## 🏪 Shopify OAuth & Management API

### **Install App**
Initiates Shopify app installation flow.

```http
GET /shopify/install?shop={store.myshopify.com}
```

**Parameters**:
- `shop` (string, required): Store domain (e.g., `mystore.myshopify.com`)

**Response**: Redirects to Shopify OAuth authorization

**Example**:
```bash
curl "https://your-app.com/shopify/install?shop=teststore.myshopify.com"
```

---

### **OAuth Callback**
Handles Shopify OAuth callback and stores access token.

```http
GET /shopify/callback?code={auth_code}&shop={store_domain}&state={nonce}
```

**Parameters**:
- `code` (string, required): OAuth authorization code
- `shop` (string, required): Store domain
- `state` (string, required): Security nonce

**Response**: Redirects to setup page

**Flow**:
1. Exchange code for access token
2. Fetch store information
3. Save store to database
4. Redirect to `/shopify/setup`

---

### **Setup Page**
Displays WhatsApp configuration form for store owners.

```http
GET /shopify/setup?shop={store_domain}
```

**Parameters**:
- `shop` (string, required): Store domain

**Response**: HTML form for WhatsApp configuration

**Features**:
- WhatsApp Access Token input
- Phone Number ID configuration  
- Business Account ID setup
- Welcome message customization

---

### **Configure WhatsApp**
Saves WhatsApp Business API credentials for a store.

```http
POST /shopify/configure?shop={store_domain}
Content-Type: application/json
```

**Request Body**:
```json
{
  "whatsapp_token": "EAAxxxxx...",
  "whatsapp_phone_number_id": "1234567890123",
  "whatsapp_business_account_id": "9876543210",
  "whatsapp_verify_token": "secure_token_123",
  "welcome_message": "👋 Welcome to our store! How can I help you today?"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "WhatsApp configuration saved"
}
```

**Schema**:
```python
class WhatsAppConfig(BaseModel):
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str
    whatsapp_business_account_id: str
    welcome_message: str = "👋 Welcome! Click 'Browse Products' to start shopping."
```

---

### **Admin Dashboard**
Store owner's management interface.

```http
GET /shopify/admin?shop={store_domain}
```

**Parameters**:
- `shop` (string, required): Store domain

**Response**: HTML dashboard with:
- Configuration status
- Usage statistics
- WhatsApp widget code
- Integration instructions

**Features**:
- Real-time status display
- Widget code generator
- Quick bot testing
- Webhook setup instructions

---

## 📱 WhatsApp Webhook API

### **Webhook Verification**
Verifies WhatsApp webhook during setup.

```http
GET /whatsapp/webhook?hub.mode=subscribe&hub.verify_token={token}&hub.challenge={challenge}
```

**Parameters**:
- `hub.mode` (string): Must be "subscribe"
- `hub.verify_token` (string): Verification token
- `hub.challenge` (string): Challenge string to return

**Response**: Returns challenge string if verification succeeds

**Example**:
```bash
curl "https://your-app.com/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=my_token&hub.challenge=123456"
# Response: 123456
```

---

### **Receive Messages**
Processes incoming WhatsApp messages and interactions.

```http
POST /whatsapp/webhook
Content-Type: application/json
X-Hub-Signature-256: sha256={signature}
```

**Request Body** (WhatsApp Format):
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "1234567890123"
            },
            "messages": [
              {
                "from": "15551234567",
                "id": "wamid.xxx",
                "timestamp": "1234567890",
                "type": "text",
                "text": {
                  "body": "Hi"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Response**:
```json
{
  "status": "ok"
}
```

**Message Types Supported**:
- `text`: Plain text messages
- `interactive`: Button/list interactions
- `button`: Button responses

**Processing Flow**:
1. Verify webhook signature
2. Extract phone_number_id from metadata
3. Find store by phone_number_id
4. Initialize WhatsApp and Shopify services
5. Process message through MessageProcessor
6. Send appropriate response

---

## 🤖 Bot Configuration API

### **Serve Registration Form**
Displays bot app registration form.

```http
GET /botapp/register
```

**Response**: HTML registration form

---

### **Register Bot App**
Saves bot application credentials.

```http
POST /botapp/register
Content-Type: application/json
```

**Request Body**:
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret", 
  "redirect_uri": "https://your-app.com/callback"
}
```

**Response**:
```json
{
  "message": "Bot app credentials saved successfully."
}
```

**Schema**:
```python
class BotAppCreateSchema(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
```

---

## 🛍️ Internal Service APIs

These are internal service methods used by the webhook processor:

### **WhatsAppService Methods**

#### **Send Text Message**
```python
async def send_message(self, to: str, message: str)
```

**Parameters**:
- `to`: Customer phone number
- `message`: Text message content

**Returns**: WhatsApp API response

---

#### **Send Button Message**
```python
async def send_button_message(self, to: str, text: str, buttons: List[Dict[str, str]])
```

**Parameters**:
- `to`: Customer phone number
- `text`: Message text
- `buttons`: List of button objects

**Button Format**:
```python
[
    {"id": "browse_products", "title": "🛍️ Browse Products"},
    {"id": "view_cart", "title": "🛒 View Cart"}
]
```

---

#### **Send List Message**
```python
async def send_list_message(self, to: str, text: str, button_text: str, sections: List[Dict])
```

**Section Format**:
```python
[{
    "title": "Available Products",
    "rows": [
        {
            "id": "product_123",
            "title": "Product Name",
            "description": "$19.99"
        }
    ]
}]
```

---

### **ShopifyService Methods**

#### **Get Products**
```python
async def get_products(self, limit: int = 10) -> List[Dict[str, Any]]
```

**Returns**:
```python
[
    {
        "id": "product_123",
        "title": "Product Name",
        "description": "Clean text description",
        "price": "19.99",
        "image": "https://cdn.shopify.com/image.jpg",
        "variant_id": "variant_456"
    }
]
```

---

#### **Get Single Product**
```python
async def get_product(self, product_id: str) -> Dict[str, Any]
```

**Returns**: Single product object with same format as above

---

#### **Create Checkout**
```python
async def create_checkout(self, line_items: List[Dict]) -> str
```

**Line Items Format**:
```python
[
    {
        "variant_id": "variant_456",
        "quantity": 2
    }
]
```

**Returns**: Shopify checkout URL

---

## 🗃️ Database Repository Methods

### **WhatsAppRepository**

#### **Get or Create Session**
```python
async def get_or_create_session(self, phone_number: str, store_url: str) -> WhatsAppSession
```

#### **Update Cart**
```python
async def update_cart(self, phone_number: str, cart_data: list)
```

**Cart Data Format**:
```python
[
    {
        "product_id": "123",
        "variant_id": "456", 
        "title": "Product Name",
        "price": "19.99",
        "quantity": 2
    }
]
```

#### **Get Cart**
```python
async def get_cart(self, phone_number: str) -> list
```

---

### **ShopifyStoreRepository**

#### **Create Store**
```python
async def create_store(self, store_url: str, access_token: str, shop_name: str) -> ShopifyStore
```

#### **Get Store by Phone Number**
```python
async def get_store_by_phone_number(self, phone_number_id: str) -> Optional[ShopifyStore]
```

#### **Update WhatsApp Config**
```python
async def update_whatsapp_config(self, store_url: str, config: dict)
```

---

## 💬 Message Processing Flow

### **Conversation States**
- `browsing`: Default state, showing main menu
- `cart`: Viewing/managing cart
- `checkout`: Completing purchase

### **Button Actions**
- `browse_products`: Show product catalog
- `view_cart`: Display cart contents
- `add_to_cart_{product_id}`: Add specific product to cart
- `checkout`: Start checkout process
- `clear_cart`: Empty cart
- `help`: Show help information

### **Text Commands**
- "hi", "hello", "hey": Trigger welcome message
- "cart": Show cart contents
- "checkout": Start checkout
- "help": Show help menu

---

## 🔒 Security & Validation

### **Webhook Signature Verification**
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

### **Input Validation**
- All API inputs validated using Pydantic models
- SQL injection protection through SQLAlchemy ORM
- XSS protection in HTML responses
- Secure random token generation

### **Rate Limiting** (Recommended)
```python
from fastapi_limiter.depends import RateLimiter

@app.post("/whatsapp/webhook")
@limiter.limit("100/minute")
async def webhook_handler():
    # Processing logic
```

---

## 🚨 Error Handling

### **Standard Error Responses**
```json
{
  "status": "error",
  "message": "Descriptive error message",
  "code": "ERROR_CODE"
}
```

### **HTTP Status Codes**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (webhook verification failed)
- `404`: Not Found (store not found)
- `500`: Internal Server Error

### **Common Errors**
- `STORE_NOT_FOUND`: Store not configured
- `WHATSAPP_DISABLED`: WhatsApp not enabled for store
- `INVALID_WEBHOOK`: Webhook verification failed
- `SHOPIFY_API_ERROR`: Shopify API request failed
- `WHATSAPP_API_ERROR`: WhatsApp API request failed

---

## 🧪 Testing

### **Webhook Testing**
```bash
# Test webhook verification
curl -X GET "https://your-app.com/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=test_token&hub.challenge=123456"

# Test message processing
curl -X POST "https://your-app.com/whatsapp/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "metadata": {"phone_number_id": "1234567890"},
          "messages": [{
            "from": "15551234567",
            "type": "text",
            "text": {"body": "Hi"}
          }]
        }
      }]
    }]
  }'
```

### **Store Installation Testing**
```bash
# Test app installation
curl "https://your-app.com/shopify/install?shop=teststore.myshopify.com"

# Test configuration
curl -X POST "https://your-app.com/shopify/configure?shop=teststore.myshopify.com" \
  -H "Content-Type: application/json" \
  -d '{
    "whatsapp_token": "test_token",
    "whatsapp_phone_number_id": "1234567890",
    "whatsapp_verify_token": "verify_token",
    "whatsapp_business_account_id": "business_id"
  }'
```

---

This API documentation provides complete reference for all endpoints and services in the WhatsApp Shopify Bot. Use the FastAPI automatic documentation at `/docs` for an interactive API explorer.