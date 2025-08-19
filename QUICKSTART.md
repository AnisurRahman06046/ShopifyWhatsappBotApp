# WhatsApp Shopping Bot - Quick Start Guide

## 🚀 Get Running in 15 Minutes

This guide will get your WhatsApp Shopping Bot up and running quickly.

## Prerequisites Checklist

- [ ] Python 3.12+
- [ ] PostgreSQL database
- [ ] Shopify Partner account
- [ ] Meta Business account with WhatsApp Business API access

## Step 1: Environment Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd ShopifyWhatsappBotApp
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Create .env file:**
```bash
# Copy example and edit
cp .env.example .env
```

3. **Configure environment variables:**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/whatsapp_shopify_bot

# Shopify (get from Partners Dashboard)
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_api_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret

# Application
SECRET_KEY=your_secret_key
REDIRECT_URI=https://your-domain.com
```

## Step 2: Database Setup

```bash
# Create database
createdb whatsapp_shopify_bot

# Run migrations
alembic upgrade head
```

## Step 3: Shopify App Configuration

1. **Go to [Shopify Partners](https://partners.shopify.com)**
2. **Create new app:**
   - App name: "WhatsApp Shopping Bot"
   - App URL: `https://your-domain.com/`
   - Allowed redirection URLs: `https://your-domain.com/shopify/callback`

3. **Set scopes:**
```
read_products,read_orders,write_orders,write_draft_orders,read_customers,write_customers
```

4. **Configure webhooks:**
```
App uninstalled: https://your-domain.com/shopify/webhooks/app/uninstalled
```

## Step 4: WhatsApp Business API Setup

1. **Create Meta Business Account:**
   - Go to [business.facebook.com](https://business.facebook.com)
   - Create or select business account
   - Add WhatsApp Business app

2. **Get credentials from WhatsApp > API Setup:**
   - Access Token (temporary or permanent)
   - Phone Number ID
   - WhatsApp Business Account ID
   - Create your own verify token

3. **Configure webhook:**
   - URL: `https://your-domain.com/whatsapp/webhook`
   - Verify Token: Your custom token
   - Subscribe to: `messages`, `messaging_postbacks`

## Step 5: Launch Application

```bash
# Start the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Install on Test Store

1. **Install on development store:**
   - Go to: `https://your-domain.com/shopify/admin?shop=your-test-store.myshopify.com`
   - Complete OAuth flow

2. **Configure WhatsApp:**
   - Enter your WhatsApp credentials
   - Set welcome message
   - Save configuration

## Step 7: Test the Bot

1. **Send test message to your WhatsApp Business number**
2. **Try the flow:**
   - Send "Hello" → Should get welcome message
   - Click "Browse Products" → Should see product list
   - Add items to cart → Should work seamlessly
   - Proceed to checkout → Should get checkout link

## 🎉 You're Live!

Your WhatsApp Shopping Bot is now running! Customers can:
- Browse your products via WhatsApp
- Manage quantities with +/- buttons
- Add items to persistent cart
- Complete checkout with secure links

## Next Steps

### Production Deployment
- Deploy to Heroku/AWS/your preferred platform
- Update environment variables for production
- Configure custom domain with SSL

### Store Submission
- Complete [full documentation](DOCUMENTATION.md) review
- Test all GDPR endpoints
- Submit to Shopify App Store

### Customization
- Customize welcome messages
- Add more product categories
- Implement advanced features

## Quick Troubleshooting

### Messages not sending?
```bash
# Test WhatsApp API connection
curl -X GET "https://graph.facebook.com/v18.0/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Products not loading?
- Check Shopify API permissions
- Verify access token is valid
- Ensure store URL format is correct

### Database issues?
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1"
```

## Support

- 📖 **Full Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
- 📧 **Email**: support@ecommercexpart.com
- 🐛 **Issues**: Create GitHub issue

---

**Need help?** The full documentation has detailed troubleshooting, API references, and advanced configuration options.