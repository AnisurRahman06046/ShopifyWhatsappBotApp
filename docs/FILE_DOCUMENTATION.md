# 📁 File-by-File Documentation

Complete documentation for each file in the WhatsApp Shopify Bot project, describing features, functions, and implementation details.

## 📂 Project Structure

```
wpBot/
├── main.py                          # FastAPI application entry point
├── config.py                        # Legacy configuration file
├── utils.py                         # Utility functions
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables
├── .env.example                    # Environment template
├── LICENSE                         # MIT License
├── README.md                       # Main documentation
├── alembic.ini                     # Database migration config
├── app/
│   ├── core/
│   │   ├── config.py               # Application configuration
│   │   ├── database.py             # Database connection setup
│   │   ├── model_loader.py         # Model loading utilities
│   │   └── redis.py                # Redis connection setup
│   ├── modules/
│   │   ├── botConfig/
│   │   │   ├── bot_models.py       # Bot configuration models
│   │   │   ├── bot_repository.py   # Bot data access layer
│   │   │   ├── bot_routes.py       # Bot configuration endpoints
│   │   │   └── bot_cache.py        # Bot caching functionality
│   │   └── whatsapp/
│   │       ├── whatsapp_models.py      # WhatsApp & Shopify models
│   │       ├── whatsapp_repository.py  # Data access layer
│   │       ├── whatsapp_service.py     # WhatsApp & Shopify APIs
│   │       ├── shopify_auth.py         # Shopify OAuth & Admin
│   │       ├── webhook_handler.py      # WhatsApp webhook processing
│   │       └── message_processor.py    # Bot conversation logic
│   └── utils/
│       └── custom_response.py      # Custom API response utilities
├── static/
│   ├── botapp_register.html        # Bot registration form
│   └── register_shop.html          # Shop registration form
├── alembic/
│   ├── versions/                   # Database migration files
│   ├── env.py                      # Alembic environment
│   └── script.py.mako              # Migration template
└── docs/
    └── FILE_DOCUMENTATION.md       # This file
```

---

## 🚀 Entry Point & Core Files

### **main.py**
**Purpose**: FastAPI application entry point and route configuration

**Key Features**:
- FastAPI app initialization with metadata
- Router inclusion for all modules
- Static file serving
- Root endpoint with API information

**Functions**:
```python
@app.get("/")
async def root()
```
- Returns basic API information and documentation link

**Dependencies**:
- FastAPI framework
- Static file serving for HTML forms
- Bot configuration routes
- WhatsApp and Shopify routes

**Usage**: Run with `uvicorn main:app --reload`

---

### **config.py** (Legacy)
**Purpose**: Legacy configuration file (not currently used)

**Note**: This file appears to be from an earlier version and is not actively used. The main configuration is in `app/core/config.py`.

---

### **utils.py**
**Purpose**: General utility functions for the application

**Functions**: (Content depends on your specific implementation)

**Usage**: Common helper functions shared across modules

---

## ⚙️ Core Configuration Files

### **app/core/config.py**
**Purpose**: Centralized application configuration using Pydantic Settings

**Key Features**:
- Environment variable loading with `.env` support
- Type validation and conversion
- Default values for development
- Secure credential handling

**Configuration Categories**:

1. **Database Settings**:
   ```python
   DATABASE_URL: str = "postgresql://postgres:anis1234@localhost/whatsapp_shopify_bot"
   REDIS_HOST: str
   REDIS_PORT: int
   ```

2. **Shopify App Credentials**:
   ```python
   SHOPIFY_API_KEY: str
   SHOPIFY_API_SECRET: str
   SHOPIFY_SCOPES: str = "read_products,read_orders,write_orders"
   ```

3. **Application Settings**:
   ```python
   ENVIRONMENT: str = "development"
   DEBUG: bool = True
   LOG_LEVEL: str = "info"
   SECRET_KEY: str
   WEBHOOK_SECRET: str = ""
   ```

4. **Payment Gateway** (BitCommerz):
   ```python
   BITCOMMERZ_TOKEN_URL: str
   BITCOMMERZ_CLIENT_ID: str
   BITCOMMERZ_CLIENT_SECRET: str
   ```

**Usage**: 
```python
from app.core.config import settings
print(settings.DATABASE_URL)
```

---

### **app/core/database.py**
**Purpose**: Async database connection and session management

**Key Features**:
- Async PostgreSQL connection using SQLAlchemy
- Database URL processing for different environments
- Session management with proper cleanup
- Base model declaration

**Components**:

1. **Connection Setup**:
   ```python
   ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
       "postgresql://", "postgresql+asyncpg://"
   )
   async_engine = create_async_engine(ASYNC_DATABASE_URL)
   ```

2. **Session Factory**:
   ```python
   AsyncSessionLocal = sessionmaker(
       async_engine, class_=AsyncSession, expire_on_commit=False
   )
   ```

3. **Dependency Injection**:
   ```python
   async def get_async_db():
       async with AsyncSessionLocal() as session:
           try:
               yield session
           finally:
               await session.close()
   ```

**Usage in Routes**:
```python
async def my_endpoint(db: AsyncSession = Depends(get_async_db)):
    # Use db session here
```

---

### **app/core/redis.py**
**Purpose**: Redis connection and caching functionality

**Features**:
- Redis connection management
- Caching utilities
- Session storage (if implemented)

---

## 🤖 Bot Configuration Module

### **app/modules/botConfig/bot_models.py**
**Purpose**: Database models for bot configuration

**Models**:

1. **BotConfig**:
   ```python
   class BotConfig(Base):
       __tablename__ = "botConfig"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       bot_clinetId = Column(String, nullable=True)
       bot_secretKey = Column(String, nullable=True)
       redirect_url = Column(String, nullable=True)
   ```

**Features**:
- UUID primary key
- OAuth client credentials storage
- Redirect URL configuration

---

### **app/modules/botConfig/bot_repository.py**
**Purpose**: Data access layer for bot configuration

**Key Methods**:
- `create_app()`: Create new bot configuration
- `get_app()`: Retrieve bot configuration
- Database CRUD operations

**Usage**: Repository pattern for clean data access

---

### **app/modules/botConfig/bot_routes.py**
**Purpose**: API endpoints for bot configuration

**Endpoints**:

1. **GET /botapp/register**:
   ```python
   @router.get("/botapp/register")
   async def serve_register_form()
   ```
   - Serves HTML registration form
   - Returns: FileResponse with registration HTML

2. **POST /botapp/register**:
   ```python
   @router.post("/botapp/register")
   async def botapp_register(data: BotAppCreateSchema, db: AsyncSession)
   ```
   - Accepts bot configuration data
   - Validates and stores credentials
   - Returns: Success confirmation

**Schema**:
```python
class BotAppCreateSchema(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
```

---

## 📱 WhatsApp Module (Core Functionality)

### **app/modules/whatsapp/whatsapp_models.py**
**Purpose**: Database models for WhatsApp sessions and Shopify stores

**Models**:

1. **WhatsAppSession**:
   ```python
   class WhatsAppSession(Base):
       __tablename__ = "whatsapp_sessions"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       phone_number = Column(String, nullable=False, unique=True)
       shopify_store_url = Column(String, nullable=False)
       session_state = Column(String, default="browsing")
       cart_data = Column(Text)  # JSON string of cart items
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   ```

2. **ShopifyStore**:
   ```python
   class ShopifyStore(Base):
       __tablename__ = "shopify_stores"
       
       # Store identification
       store_url = Column(String, nullable=False, unique=True)
       access_token = Column(String, nullable=False)
       shop_name = Column(String, nullable=False)
       
       # WhatsApp configuration
       whatsapp_enabled = Column(Boolean, default=False)
       whatsapp_token = Column(String, nullable=True)
       whatsapp_phone_number_id = Column(String, nullable=True)
       whatsapp_verify_token = Column(String, nullable=True)
       whatsapp_business_account_id = Column(String, nullable=True)
       
       # Customization
       welcome_message = Column(Text, default="👋 Welcome! Click 'Browse Products' to start shopping.")
   ```

**Features**:
- Customer session tracking
- Store-specific WhatsApp credentials
- Cart persistence
- Session state management

---

### **app/modules/whatsapp/whatsapp_repository.py**
**Purpose**: Data access layer for WhatsApp and Shopify data

**Repository Classes**:

1. **WhatsAppRepository**:
   ```python
   async def get_or_create_session(phone_number: str, store_url: str) -> WhatsAppSession
   async def update_session_state(phone_number: str, state: str)
   async def update_cart(phone_number: str, cart_data: list)
   async def get_cart(phone_number: str) -> list
   ```

2. **ShopifyStoreRepository**:
   ```python
   async def create_store(store_url: str, access_token: str, shop_name: str) -> ShopifyStore
   async def get_store_by_url(store_url: str) -> Optional[ShopifyStore]
   async def get_store_by_phone_number(phone_number_id: str) -> Optional[ShopifyStore]
   async def update_whatsapp_config(store_url: str, config: dict)
   ```

**Key Features**:
- Async database operations
- Session management
- Store configuration handling
- Cart data persistence (JSON format)

---

### **app/modules/whatsapp/whatsapp_service.py**
**Purpose**: Integration with WhatsApp Business API and Shopify Admin API

**Service Classes**:

1. **WhatsAppService**:
   ```python
   def __init__(self, store_config):
       self.token = store_config.whatsapp_token
       self.phone_number_id = store_config.whatsapp_phone_number_id
   ```

   **Methods**:
   - `send_message()`: Send text messages
   - `send_button_message()`: Interactive buttons
   - `send_list_message()`: Product lists
   - `send_product_message()`: Product details

2. **ShopifyService**:
   ```python
   def __init__(self, store_url: str, access_token: str):
       self.store_url = store_url
       self.access_token = access_token
   ```

   **Methods**:
   - `get_products()`: Fetch store products
   - `get_product()`: Get single product
   - `create_checkout()`: Generate checkout URL

**API Integration Features**:
- Store-specific credentials
- HTML tag cleaning for descriptions
- Error handling and logging
- Async HTTP requests with httpx

---

### **app/modules/whatsapp/shopify_auth.py**
**Purpose**: Shopify OAuth flow and admin interface

**Key Endpoints**:

1. **OAuth Flow**:
   ```python
   @router.get("/shopify/install")
   async def install_shopify_app(shop: str = Query(...))
   
   @router.get("/shopify/callback")
   async def shopify_callback(code: str, shop: str, state: str, db: AsyncSession)
   ```

2. **Configuration**:
   ```python
   @router.post("/shopify/configure")
   async def configure_whatsapp(config: WhatsAppConfig, shop: str, db: AsyncSession)
   ```

3. **Admin Interface**:
   ```python
   @router.get("/shopify/setup")
   async def setup_page(shop: str, db: AsyncSession)
   
   @router.get("/shopify/admin")
   async def admin_dashboard(shop: str, db: AsyncSession)
   ```

**Features**:
- Secure OAuth implementation
- Beautiful HTML interfaces
- WhatsApp credential configuration
- Widget code generation
- Usage statistics display

---

### **app/modules/whatsapp/webhook_handler.py**
**Purpose**: Process incoming WhatsApp webhooks

**Key Functions**:

1. **Webhook Verification**:
   ```python
   @router.get("/whatsapp/webhook")
   async def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str)
   ```

2. **Message Processing**:
   ```python
   @router.post("/whatsapp/webhook")
   async def receive_message(request: Request, db: AsyncSession)
   ```

3. **Message Routing**:
   ```python
   async def handle_messages(value: dict, db: AsyncSession):
       # 1. Extract phone_number_id from webhook
       # 2. Find store by phone_number_id
       # 3. Initialize services with store credentials
       # 4. Process each message
   ```

**Processing Flow**:
1. Webhook authentication
2. Store identification by phone number
3. Service initialization
4. Message type detection
5. Route to appropriate handler

**Supported Message Types**:
- Text messages
- Interactive button responses
- List selections

---

### **app/modules/whatsapp/message_processor.py**
**Purpose**: Core bot conversation logic and shopping flow

**Main Class**: `MessageProcessor`

**Key Methods**:

1. **Text Processing**:
   ```python
   async def process_text_message(self, from_number: str, text: str, session)
   ```
   - Handles greetings ("hi", "hello")
   - Cart commands
   - Help requests

2. **Interactive Processing**:
   ```python
   async def process_interactive_message(self, from_number: str, interactive: dict, session)
   async def process_button_response(self, from_number: str, button: dict, session)
   ```

3. **Shopping Flow**:
   ```python
   async def send_welcome_message(self, from_number: str)
   async def show_products(self, from_number: str)
   async def show_product_details(self, from_number: str, product_id: str)
   async def add_to_cart(self, from_number: str, product_id: str, session)
   async def show_cart(self, from_number: str, session)
   async def start_checkout(self, from_number: str, session)
   ```

**Button Action Handlers**:
- `browse_products`: Show product catalog
- `view_cart`: Display cart contents
- `add_to_cart_*`: Add specific product
- `checkout`: Generate checkout link
- `clear_cart`: Empty cart

**Shopping Flow Logic**:
1. Welcome → Browse Products
2. Product List → Product Details
3. Add to Cart → Cart Management
4. Checkout → Shopify Payment

---

## 🎨 Static Files

### **static/botapp_register.html**
**Purpose**: HTML form for bot app registration

**Features**:
- Client ID/Secret input
- Redirect URI configuration
- Form validation
- Responsive design

---

### **static/register_shop.html**
**Purpose**: Shop registration interface

**Features**:
- Shop URL validation
- Registration form
- Success/error handling

---

## 🗃️ Database Migrations

### **alembic.ini**
**Purpose**: Alembic configuration for database migrations

**Settings**:
- Database URL configuration
- Migration file location
- Version table settings

### **alembic/env.py**
**Purpose**: Alembic environment configuration

**Features**:
- Async database support
- Model metadata import
- Migration execution logic

### **alembic/versions/**
**Purpose**: Database migration files

**Content**: Auto-generated migration scripts for schema changes

---

## 🔧 Configuration Files

### **.env**
**Purpose**: Environment variables for local development

**Categories**:
- Database credentials
- API keys and secrets
- App configuration
- Debug settings

### **.env.example**
**Purpose**: Template for environment variables

**Usage**: Copy to `.env` and fill in actual values

### **requirements.txt**
**Purpose**: Python package dependencies

**Key Dependencies**:
- `fastapi`: Web framework
- `sqlalchemy`: Database ORM
- `asyncpg`: PostgreSQL async driver
- `httpx`: HTTP client
- `pydantic`: Data validation
- `redis`: Caching
- `alembic`: Database migrations

---

## 📚 Documentation Files

### **LICENSE**
**Purpose**: MIT License for the project

### **README.md**
**Purpose**: Main project documentation

**Sections**:
- Architecture overview
- Quick start guide
- API documentation
- Deployment instructions

---

This comprehensive file documentation covers every aspect of the WhatsApp Shopify Bot project, making it easy for developers to understand and contribute to the codebase.