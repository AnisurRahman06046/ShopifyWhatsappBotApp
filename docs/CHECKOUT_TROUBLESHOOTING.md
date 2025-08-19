# WhatsApp Bot Checkout Troubleshooting Guide

## Problem Overview

The WhatsApp bot's checkout functionality was not working due to deprecated Shopify APIs and inadequate error handling.

## Symptoms

- Users clicking "Checkout" button received error messages
- No checkout URLs were generated
- Cart items would disappear without completing purchase
- Generic "error creating checkout" messages

## Root Causes Identified

### 1. Deprecated Shopify Checkout API
**Issue**: The code was using Shopify's deprecated `checkouts.json` API endpoint.
```python
# OLD - DEPRECATED
url = f"{self.base_url}/checkouts.json"
```

**Why it failed**: Shopify deprecated this API in favor of newer methods like Draft Orders and Storefront API.

### 2. Outdated API Version
**Issue**: Using API version `2023-10` instead of the latest `2024-01`.
```python
# OLD
self.base_url = f"https://{store_url}/admin/api/2023-10"
```

### 3. Missing Error Handling
**Issue**: No validation for cart items missing `variant_id` field.
```python
# OLD - No validation
line_items = [
    {
        "variant_id": item["variant_id"],  # Could be None
        "quantity": item["quantity"]
    }
    for item in cart
]
```

### 4. Single Point of Failure
**Issue**: Only one checkout method with no fallback options.

## Solutions Implemented

### 1. Updated to Modern Shopify APIs

#### Primary Method: Cart Permalink URLs
```python
async def create_cart_permalink(self, line_items: List[Dict]) -> str:
    """Create a cart permalink URL for checkout"""
    cart_params = []
    for item in line_items:
        cart_params.append(f"{item['variant_id']}:{item['quantity']}")
    
    cart_string = ",".join(cart_params)
    checkout_url = f"https://{self.store_url}/cart/{cart_string}"
    return checkout_url
```

**Benefits**:
- Instant checkout URL generation
- No API calls required
- Always works if variant IDs are valid
- Compatible with all Shopify stores

#### Fallback Method: Draft Orders API
```python
async def create_draft_order_checkout(self, line_items: List[Dict]) -> str:
    """Create a draft order and get checkout URL"""
    url = f"{self.base_url}/draft_orders.json"
    data = {
        "draft_order": {
            "line_items": draft_line_items,
            "note": "Order from WhatsApp Bot",
            "use_customer_default_address": True
        }
    }
    # ... API call and response handling
```

**Benefits**:
- More control over checkout process
- Can add custom notes and settings
- Works when cart permalinks fail

### 2. Enhanced Error Handling

#### Cart Item Validation
```python
# Validate cart items have variant_id
valid_items = []
for item in cart:
    if item.get("variant_id"):
        valid_items.append({
            "variant_id": item["variant_id"],
            "quantity": item["quantity"]
        })
    else:
        print(f"[WARNING] Cart item missing variant_id: {item}")

if not valid_items:
    await self.whatsapp.send_message(
        to=from_number,
        message="Sorry, there was an issue with your cart items. Please try adding them again."
    )
    return
```

#### Exception Handling
```python
try:
    checkout_url = await self.shopify.create_checkout(valid_items)
    if checkout_url:
        # Success message
    else:
        # Fallback error message
except Exception as e:
    print(f"[ERROR] Checkout creation failed: {str(e)}")
    # User-friendly error message
```

### 3. Multiple Fallback Strategy

The new checkout system follows this hierarchy:

1. **Cart Permalink** (Primary) - Fast, reliable
2. **Draft Order with Invoice URL** (Secondary)
3. **Draft Order with Cart Fallback** (Tertiary)
4. **Basic Cart URL Construction** (Last Resort)

```python
async def create_checkout(self, line_items: List[Dict]) -> str:
    """Create checkout using multiple methods"""
    
    # Method 1: Try creating a permalink cart URL
    cart_url = await self.create_cart_permalink(line_items)
    if cart_url:
        return cart_url
    
    # Method 2: Fallback to draft order
    return await self.create_draft_order_checkout(line_items)
```

### 4. Updated API Version
```python
# NEW
self.base_url = f"https://{store_url}/admin/api/2024-01"
```

## Files Modified

### 1. `app/modules/whatsapp/whatsapp_service.py`
- **Line 112**: Updated API version to 2024-01
- **Lines 199-314**: Complete rewrite of checkout functionality
- Added methods: `create_checkout()`, `create_cart_permalink()`, `create_draft_order_checkout()`

### 2. `app/modules/whatsapp/message_processor.py`
- **Lines 273-313**: Enhanced `start_checkout()` method
- Added cart item validation
- Added comprehensive error handling
- Improved user messaging

## Testing the Fix

### Manual Testing Steps

1. **Start the bot**: `uvicorn main:app --reload`

2. **Test cart addition**:
   - Send "Hi" to bot
   - Click "Browse Products"
   - Select a product
   - Click "Add to Cart"

3. **Test checkout**:
   - Click "View Cart"
   - Click "Checkout"
   - Verify you receive a working checkout URL

### Expected Behaviors

#### Success Case
```
🎉 Your checkout is ready!

Click this link to complete your purchase:
https://yourstore.myshopify.com/cart/123456789:1,987654321:2

Thank you for shopping with us!
```

#### Error Cases
```
# Missing variant IDs
"Sorry, there was an issue with your cart items. Please try adding them again."

# API failures
"Sorry, there was an error processing your checkout. Our team has been notified. Please try again later."

# Empty cart
"Your cart is empty. Add some products first!"
```

## Monitoring and Debugging

### Debug Logs to Watch
```bash
# Success indicators
[DEBUG] Created cart permalink: https://store.com/cart/123:1
[DEBUG] Generated draft order URL: https://store.com/draft_orders/token

# Error indicators
[ERROR] Failed to create draft order: {"error": "..."}
[WARNING] Cart item missing variant_id: {...}
[ERROR] Checkout creation failed: Connection error
```

### Log Locations
- Console output when running with `uvicorn main:app --reload`
- Check for print statements in the code

## Prevention Strategies

### 1. Regular API Version Updates
- Check Shopify's API changelog quarterly
- Update API versions in `whatsapp_service.py`
- Test checkout functionality after updates

### 2. Monitoring Setup
Consider adding:
```python
import logging

logger = logging.getLogger(__name__)

# In checkout methods
logger.error(f"Checkout failed for user {from_number}: {str(e)}")
logger.info(f"Successful checkout created: {checkout_url}")
```

### 3. Automated Testing
Create test cases for:
- Cart with valid items
- Cart with missing variant_ids
- API failure scenarios
- Empty cart scenarios

### 4. User Experience Improvements
- Add loading messages: "⏳ Creating your checkout..."
- Provide alternative contact methods on failure
- Implement retry mechanisms

## Related Documentation

- [Shopify Admin API - Draft Orders](https://shopify.dev/docs/api/admin-rest/2024-01/resources/draftorder)
- [Shopify Cart Permalinks](https://shopify.dev/docs/themes/liquid/objects/cart#cart-url)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api)

## Troubleshooting Common Issues

### Issue: "Cart permalink not working"
**Cause**: Invalid variant IDs or store settings
**Solution**: 
1. Verify variant IDs exist in store
2. Check store's cart settings
3. Test with draft order fallback

### Issue: "Draft order creation fails"
**Cause**: Invalid access token or permissions
**Solution**:
1. Verify Shopify access token
2. Check app permissions include `write_draft_orders`
3. Test API connection with simple GET request

### Issue: "All checkout methods fail"
**Cause**: Network issues or store configuration
**Solution**:
1. Check internet connectivity
2. Verify store URL format
3. Test with minimal cart (1 item)
4. Check Shopify store status

## Version History

- **v1.0** (2025-08-19): Initial fix implementation
  - Replaced deprecated checkout API
  - Added cart permalink method
  - Enhanced error handling
  - Updated to API version 2024-01