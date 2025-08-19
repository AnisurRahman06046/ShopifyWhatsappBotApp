# WhatsApp Bot Quantity Management Feature

## Overview

This document describes the quantity management system implemented in the WhatsApp bot, allowing users to increase/decrease product quantities before adding to cart and manage quantities within their cart.

## Features Implemented

### 1. Product Quantity Selection
- Users can adjust quantity before adding products to cart
- Displays real-time price calculation based on quantity
- Quantity limits: 1 minimum, 99 maximum

### 2. Cart Quantity Management
- Modify quantities of items already in cart
- Remove items by reducing quantity to 0
- Real-time cart total updates

### 3. Smart Cart Display
- Single item carts show detailed controls immediately
- Multiple item carts show list for item selection
- Clear visual feedback for all actions

## User Experience Flow

### Product Browsing with Quantity Control

1. **User selects a product** → Shows product details with quantity 1
2. **User clicks "➕ More"** → Quantity increases, price updates
3. **User clicks "➖ Less"** → Quantity decreases (minimum 1)
4. **User clicks "🛒 Add X to Cart"** → Adds specified quantity to cart

**Example Display:**
```
🛍️ Premium T-Shirt

💰 Price: $25.00
📝 High-quality cotton t-shirt with premium finish...

📦 Quantity: 3
💵 Total: $75.00

[➖ Less] [➕ More] [🛒 Add 3 to Cart]
```

### Cart Management

#### Single Item Cart
Shows detailed controls immediately:
```
🛍️ Premium T-Shirt

💰 Price: $25.00 each
📦 Quantity: 3
💵 Subtotal: $75.00

[➖ Remove 1] [➕ Add 1] [🛒 Back to Cart]
```

#### Multiple Item Cart
Shows item selection list:
```
🛒 Your Cart (3 items):

💰 Total: $125.00

Select an item to adjust quantity:

[Manage Items ▼]
• Premium T-Shirt (×3) - $75.00
• Jeans (×1) - $50.00

Choose an action:
[💳 Checkout] [🛍️ Add More] [🗑️ Clear Cart]
```

## Technical Implementation

### Files Modified

#### 1. `app/modules/whatsapp/whatsapp_service.py`

**Method: `send_product_message()`** (Lines 93-109)
- Added `quantity` parameter with default value 1
- Displays quantity and calculated total price
- Creates quantity control buttons

```python
async def send_product_message(self, to: str, product: Dict[str, Any], quantity: int = 1):
    text = f"🛍️ *{product['title']}*\n\n"
    text += f"💰 Price: ${product['price']}\n"
    text += f"📝 {product['description'][:200]}...\n"
    text += f"\n📦 Quantity: {quantity}\n"
    text += f"💵 Total: ${float(product['price']) * quantity:.2f}"
    
    buttons = [
        {"id": f"qty_decrease_{product['id']}_{quantity}", "title": "➖ Less"},
        {"id": f"qty_increase_{product['id']}_{quantity}", "title": "➕ More"},
        {"id": f"add_to_cart_{product['id']}_{quantity}", "title": f"🛒 Add {quantity} to Cart"}
    ]
```

#### 2. `app/modules/whatsapp/message_processor.py`

**Enhanced Button Handling** (Lines 102-134)
- `qty_increase_` - Increases product quantity
- `qty_decrease_` - Decreases product quantity  
- `cart_qty_increase_` - Increases cart item quantity
- `cart_qty_decrease_` - Decreases cart item quantity

**Method: `add_to_cart()`** (Lines 214-268)
- Added quantity parameter
- Handles adding specific quantities
- Provides better confirmation messages

**Method: `update_cart_quantity()`** (Lines 270-297)
- Updates quantities of existing cart items
- Removes items when quantity reaches 0
- Refreshes cart display after changes

**Method: `show_cart()`** (Lines 299-356)
- Smart display based on cart size
- List interface for multiple items
- Direct controls for single items

**Method: `show_cart_item_details()`** (Lines 358-378)
- Detailed view of individual cart items
- Quantity controls for cart management

## Button ID Patterns

### Product Quantity Controls
- `qty_increase_{product_id}_{current_quantity}` - Increase product quantity
- `qty_decrease_{product_id}_{current_quantity}` - Decrease product quantity
- `add_to_cart_{product_id}_{quantity}` - Add specific quantity to cart

### Cart Quantity Controls
- `cart_qty_increase_{product_id}` - Add 1 to cart item
- `cart_qty_decrease_{product_id}` - Remove 1 from cart item
- `cart_item_{product_id}` - Select cart item for management

## Quantity Limits and Validation

### Product Selection
- **Minimum**: 1 item
- **Maximum**: 99 items
- **Increment**: 1 item per button press

### Cart Management
- **Minimum**: 1 item (0 removes from cart)
- **Maximum**: 99 items total per product
- **Auto-removal**: Items with quantity 0 are removed

## Error Handling

### Invalid Quantities
```python
new_qty = min(current_qty + 1, 99)  # Max limit
new_qty = max(current_qty - 1, 1)   # Min limit
```

### Missing Cart Items
```python
if not item_to_update:
    await self.whatsapp.send_message(
        to=from_number,
        message="Item not found in cart."
    )
    return
```

### Quantity Removal
```python
if new_quantity <= 0:
    # Remove item from cart
    cart = [item for item in cart if item["product_id"] != product_id]
    await self.whatsapp.send_message(
        to=from_number,
        message=f"🗑️ Removed '{item_to_update['title']}' from your cart."
    )
```

## Testing Scenarios

### Basic Quantity Flow
1. Browse products → Select product → Increase quantity → Add to cart
2. View cart → Select item → Modify quantity → Verify updates

### Edge Cases
1. **Minimum quantity**: Try to decrease below 1
2. **Maximum quantity**: Try to increase above 99
3. **Cart removal**: Decrease cart item to 0
4. **Empty cart**: Remove all items

### Expected Behaviors

#### Successful Operations
- Quantity changes update display immediately
- Price calculations are accurate
- Cart totals update correctly
- Clear confirmation messages

#### Error Prevention
- Cannot go below quantity 1 in product view
- Cannot exceed quantity 99
- Graceful handling of missing items
- Auto-removal of zero-quantity items

## Future Enhancements

### Possible Improvements
1. **Bulk quantity input**: Allow typing specific quantities
2. **Stock validation**: Check product availability
3. **Quantity presets**: Quick buttons for common quantities (5, 10, etc.)
4. **Wishlist integration**: Save for later functionality
5. **Quantity history**: Track popular quantities per product

### Advanced Features
1. **Inventory alerts**: Notify when low stock
2. **Bulk discounts**: Show savings for larger quantities
3. **Shipping calculations**: Factor quantity into shipping costs
4. **Cart persistence**: Save quantities across sessions

## Troubleshooting

### Common Issues

#### Quantity buttons not working
**Cause**: Button ID parsing errors
**Solution**: Check button ID format in logs

#### Cart not updating
**Cause**: Database connection issues
**Solution**: Verify repository methods and database connectivity

#### Price calculations incorrect
**Cause**: String/float conversion issues
**Solution**: Ensure proper type casting in calculations

### Debug Information

Enable debug logging to track:
```python
print(f"[DEBUG] Quantity change: {product_id} -> {new_quantity}")
print(f"[DEBUG] Cart after update: {cart}")
print(f"[DEBUG] Button ID parsed: {button_id} -> {parts}")
```

## Version History

- **v1.0** (2025-08-19): Initial quantity management implementation
  - Product quantity selection before adding to cart
  - Cart item quantity modification
  - Smart cart display based on item count
  - Comprehensive error handling and validation