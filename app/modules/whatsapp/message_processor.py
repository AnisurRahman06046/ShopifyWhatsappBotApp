import json
from typing import Dict, List, Any
from .product_repository import ProductRepository


class MessageProcessor:
    def __init__(self, whatsapp_service, shopify_service, whatsapp_repo, store, db_session=None):
        self.whatsapp = whatsapp_service
        self.shopify = shopify_service
        self.repo = whatsapp_repo
        self.store = store
        self.db_session = db_session
        self.product_repo = ProductRepository(db_session) if db_session else None

    async def process_text_message(self, from_number: str, text: str, session):
        """Process text messages from customers"""
        
        text = text.lower().strip()
        
        # Handle greetings
        if any(greeting in text for greeting in ["hi", "hello", "hey", "start"]):
            await self.send_welcome_message(from_number)
        
        # Handle cart commands
        elif "cart" in text:
            await self.show_cart(from_number, session)
        
        # Handle checkout
        elif "checkout" in text:
            await self.start_checkout(from_number, session)
        
        # Handle help
        elif "help" in text or "?" in text:
            await self.send_help_message(from_number)
        
        # Default: show main menu
        else:
            await self.send_main_menu(from_number)

    async def process_interactive_message(self, from_number: str, interactive: dict, session):
        """Process interactive button/list responses"""
        
        interactive_type = interactive.get("type")
        
        if interactive_type == "button_reply":
            button_reply = interactive.get("button_reply", {})
            button_id = button_reply.get("id", "")
            
            await self.handle_button_action(from_number, button_id, session)
        
        elif interactive_type == "list_reply":
            list_reply = interactive.get("list_reply", {})
            item_id = list_reply.get("id", "")
            
            await self.handle_list_selection(from_number, item_id, session)

    async def process_button_response(self, from_number: str, button: dict, session):
        """Process button responses"""
        
        payload = button.get("payload", "")
        await self.handle_button_action(from_number, payload, session)

    async def send_welcome_message(self, from_number: str):
        """Send welcome message with main menu"""
        
        buttons = [
            {"id": "browse_products", "title": "🛍️ Browse Products"},
            {"id": "view_cart", "title": "🛒 View Cart"},
            {"id": "help", "title": "❓ Help"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text=self.store.welcome_message,
            buttons=buttons
        )

    async def send_main_menu(self, from_number: str):
        """Send main menu options"""
        
        buttons = [
            {"id": "browse_products", "title": "🛍️ Browse Products"},
            {"id": "view_cart", "title": "🛒 View Cart"},
            {"id": "contact_support", "title": "💬 Contact Support"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text="What would you like to do?",
            buttons=buttons
        )

    async def handle_button_action(self, from_number: str, button_id: str, session):
        """Handle button click actions"""
        
        if button_id == "browse_products":
            await self.show_products(from_number)
        
        elif button_id == "view_cart":
            await self.show_cart(from_number, session)
        
        elif button_id == "help":
            await self.send_help_message(from_number)
        
        elif button_id.startswith("add_to_cart_"):
            parts = button_id.replace("add_to_cart_", "").split("_")
            product_id = parts[0]
            quantity = int(parts[1]) if len(parts) > 1 else 1
            await self.add_to_cart(from_number, product_id, session, quantity)
        
        elif button_id.startswith("view_product_"):
            product_id = button_id.replace("view_product_", "")
            await self.show_product_details(from_number, product_id)
        
        elif button_id.startswith("qty_increase_"):
            parts = button_id.replace("qty_increase_", "").split("_")
            product_id = parts[0]
            current_qty = int(parts[1]) if len(parts) > 1 else 1
            new_qty = min(current_qty + 1, 99)  # Max quantity limit
            await self.show_product_details(from_number, product_id, new_qty)
        
        elif button_id.startswith("qty_decrease_"):
            parts = button_id.replace("qty_decrease_", "").split("_")
            product_id = parts[0]
            current_qty = int(parts[1]) if len(parts) > 1 else 1
            new_qty = max(current_qty - 1, 1)  # Min quantity is 1
            await self.show_product_details(from_number, product_id, new_qty)
        
        elif button_id.startswith("cart_qty_increase_"):
            parts = button_id.replace("cart_qty_increase_", "").split("_")
            product_id = parts[0]
            await self.update_cart_quantity(from_number, product_id, 1, session)
        
        elif button_id.startswith("cart_qty_decrease_"):
            parts = button_id.replace("cart_qty_decrease_", "").split("_")
            product_id = parts[0]
            await self.update_cart_quantity(from_number, product_id, -1, session)
        
        elif button_id == "checkout":
            await self.start_checkout(from_number, session)
        
        elif button_id == "clear_cart":
            await self.clear_cart(from_number, session)
        
        else:
            await self.send_main_menu(from_number)

    async def handle_list_selection(self, from_number: str, item_id: str, session):
        """Handle list item selection"""
        
        if item_id.startswith("product_"):
            product_id = item_id.replace("product_", "")
            await self.show_product_details(from_number, product_id)
        
        elif item_id.startswith("category_"):
            category = item_id.replace("category_", "")
            await self.show_products_by_category(from_number, category)
        
        elif item_id.startswith("cart_item_"):
            product_id = item_id.replace("cart_item_", "")
            # Get the cart item and show details
            cart = await self.repo.get_cart(from_number)
            cart_item = next((item for item in cart if item["product_id"] == product_id), None)
            
            if cart_item:
                await self.show_cart_item_details(from_number, cart_item, session)
            else:
                await self.whatsapp.send_message(
                    to=from_number,
                    message="Item not found in cart."
                )

    async def show_products(self, from_number: str, page: int = 1):
        """Display product catalog from database (NO API CALLS!)"""
        
        if not self.product_repo:
            # Fallback to old method if no db session
            products = await self.shopify.get_products(limit=10)
            return await self._show_products_fallback(from_number, products)
        
        try:
            # Get ALL products from database instead of Shopify API (no pagination)
            result = await self.product_repo.get_products_for_browsing(
                store_id=self.store.id, 
                page=1, 
                limit=100  # Show all products at once
            )
            
            products = result["products"]
            
            if not products:
                await self.whatsapp.send_message(
                    to=from_number,
                    message="Sorry, no products available at the moment. Our products may still be syncing."
                )
                return
            
            # Check if products have variants - if not, fallback to Shopify API temporarily
            products_with_variants = [p for p in products if p.variants]
            if len(products_with_variants) == 0:
                print("[WARNING] No variants found in database, falling back to Shopify API")
                shopify_products = await self.shopify.get_products(limit=20)
                return await self._show_products_fallback(from_number, shopify_products)
            
            # Use same single-section format as working API fallback
            sections = [{
                "title": "Available Products",
                "rows": []
            }]
            
            for product in products[:10]:  # Limit to 10 products like API fallback
                # Get the first variant for pricing
                first_variant = product.variants[0] if product.variants else None
                if first_variant:
                    price_text = f"${first_variant.price:.2f}"
                    print(f"[DEBUG] Product {product.title}: price=${first_variant.price}, variant_id={first_variant.shopify_variant_id}")
                else:
                    price_text = "Price on request"
                    print(f"[DEBUG] Product {product.title}: NO VARIANTS FOUND")
                
                sections[0]["rows"].append({
                    "id": f"product_{product.shopify_product_id}",
                    "title": product.title[:24],  # WhatsApp limit
                    "description": price_text
                })
            
            # Simple product listing without pagination
            nav_text = f"📦 Here are our available products:"
            
            print(f"[DEBUG] Attempting to send list message with {len(sections)} sections")
            print(f"[DEBUG] Section details: {[(s['title'], len(s['rows'])) for s in sections]}")
            
            try:
                await self.whatsapp.send_list_message(
                    to=from_number,
                    text=nav_text,
                    button_text="View Products",
                    sections=sections
                )
                print(f"[DEBUG] WhatsApp list message sent successfully")
            except Exception as e:
                print(f"[ERROR] Failed to send WhatsApp list message: {str(e)}")
                # Fallback: send simple text message
                product_list = "\n".join([f"• {p.title} - ${p.variants[0].price:.2f}" for p in products[:10] if p.variants])
                await self.whatsapp.send_message(
                    to=from_number,
                    message=f"📦 Our Products:\n\n{product_list}\n\nReply with product name to view details"
                )
            
            print(f"[INFO] ✅ Served {len(products)} products from database (NO API CALL)")
            
        except Exception as e:
            print(f"[ERROR] Failed to get products from database: {str(e)}")
            # Fallback to Shopify API
            products = await self.shopify.get_products(limit=10)
            await self._show_products_fallback(from_number, products)
    
    async def _show_products_fallback(self, from_number: str, products: list):
        """Fallback method using Shopify API"""
        print("[WARNING] Using Shopify API fallback for products")
        
        if not products:
            await self.whatsapp.send_message(
                to=from_number,
                message="Sorry, no products available at the moment."
            )
            return
        
        sections = [{
            "title": "Available Products",
            "rows": []
        }]
        
        for product in products[:10]:
            sections[0]["rows"].append({
                "id": f"product_{product['id']}",
                "title": product["title"][:24],
                "description": f"${product['price']}"
            })
        
        await self.whatsapp.send_list_message(
            to=from_number,
            text="📦 Here are our available products:",
            button_text="View Products",
            sections=sections
        )

    async def show_product_details(self, from_number: str, product_id: str, quantity: int = 1):
        """Show detailed product information with quantity controls from database"""
        
        if not self.product_repo:
            # Fallback to Shopify API
            product = await self.shopify.get_product(product_id)
            if not product:
                await self.whatsapp.send_message(
                    to=from_number,
                    message="Sorry, product not found."
                )
                return
            await self.whatsapp.send_product_message(from_number, product, quantity)
            return
        
        try:
            # Get product from database instead of Shopify API
            product = await self.product_repo.get_product_by_id(self.store.id, product_id)
            
            if not product:
                await self.whatsapp.send_message(
                    to=from_number,
                    message="Sorry, product not found."
                )
                return
            
            # Convert database product to format expected by WhatsApp service
            product_data = self._convert_db_product_to_whatsapp_format(product)
            await self.whatsapp.send_product_message(from_number, product_data, quantity)
            
            print(f"[INFO] ✅ Served product details from database (NO API CALL)")
            
        except Exception as e:
            print(f"[ERROR] Failed to get product details from database: {str(e)}")
            # Fallback to Shopify API
            product = await self.shopify.get_product(product_id)
            if not product:
                await self.whatsapp.send_message(
                    to=from_number,
                    message="Sorry, product not found."
                )
                return
            await self.whatsapp.send_product_message(from_number, product, quantity)
    
    def _convert_db_product_to_whatsapp_format(self, db_product) -> dict:
        """Convert database product to format expected by WhatsApp service"""
        
        # Get the first variant for pricing and variant_id
        first_variant = db_product.variants[0] if db_product.variants else None
        
        # Get the first image
        first_image = db_product.images[0] if db_product.images else None
        
        result = {
            "id": db_product.shopify_product_id,  # Use Shopify ID consistently
            "shopify_id": db_product.shopify_product_id,  # Keep Shopify ID for cart/checkout
            "title": db_product.title,
            "description": db_product.description or "",
            "price": first_variant.price if first_variant else 0.0,
            "variant_id": first_variant.shopify_variant_id if first_variant else None,
            "image_url": first_image.image_url if first_image else None,
            "inventory_quantity": first_variant.inventory_quantity if first_variant else 0,
            "available": first_variant.available if first_variant else False
        }
        print(f"[DEBUG] Converted product {db_product.title}: price=${result['price']}, variant_id={result['variant_id']}")
        return result

    async def add_to_cart(self, from_number: str, product_id: str, session, quantity: int = 1):
        """Add product to cart with specified quantity"""
        
        # Get current cart
        cart = await self.repo.get_cart(from_number)
        
        # Get product details (try database first, then Shopify API)
        product = None
        
        if self.product_repo:
            try:
                # Get from database first
                db_product = await self.product_repo.get_product_by_id(self.store.id, product_id)
                if db_product:
                    product = self._convert_db_product_to_whatsapp_format(db_product)
                    print(f"[INFO] ✅ Got product for cart from database (NO API CALL)")
            except Exception as e:
                print(f"[ERROR] Failed to get product from database for cart: {str(e)}")
        
        # Fallback to Shopify API if database lookup failed
        if not product:
            print("[WARNING] Using Shopify API fallback for add_to_cart")
            product = await self.shopify.get_product(product_id)
        
        if not product:
            await self.whatsapp.send_message(
                to=from_number,
                message="Sorry, product not found."
            )
            return
        
        # Add to cart
        cart_item = {
            "product_id": product["id"],
            "variant_id": product["variant_id"],
            "title": product["title"],
            "price": product["price"],
            "quantity": quantity
        }
        
        # Check if product already in cart
        existing_item = next((item for item in cart if item["product_id"] == product_id), None)
        
        if existing_item:
            existing_item["quantity"] += quantity
        else:
            cart.append(cart_item)
        
        # Update cart in database
        await self.repo.update_cart(from_number, cart)
        
        # Send confirmation
        cart = await self.repo.get_cart(from_number)  # Get updated cart
        updated_item = next((item for item in cart if item["product_id"] == product_id), None)
        total_quantity = updated_item["quantity"] if updated_item else quantity
        quantity_text = f"{quantity}" if quantity == 1 else f"{quantity} items"
        
        buttons = [
            {"id": "view_cart", "title": "🛒 View Cart"},
            {"id": "browse_products", "title": "🛍️ Continue Shopping"},
            {"id": "checkout", "title": "💳 Checkout"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text=f"✅ Added {quantity_text} of '{product['title']}' to your cart!\n\n📦 Total in cart: {total_quantity}",
            buttons=buttons
        )

    async def update_cart_quantity(self, from_number: str, product_id: str, quantity_change: int, session):
        """Update quantity of item in cart"""
        
        cart = await self.repo.get_cart(from_number)
        
        # Find the item in cart
        item_to_update = next((item for item in cart if item["product_id"] == product_id), None)
        
        if not item_to_update:
            await self.whatsapp.send_message(
                to=from_number,
                message="Item not found in cart."
            )
            return
        
        # Update quantity
        new_quantity = item_to_update["quantity"] + quantity_change
        
        if new_quantity <= 0:
            # Remove item from cart
            cart = [item for item in cart if item["product_id"] != product_id]
            await self.repo.update_cart(from_number, cart)
            await self.whatsapp.send_message(
                to=from_number,
                message=f"🗑️ Removed '{item_to_update['title']}' from your cart."
            )
        else:
            # Update quantity
            item_to_update["quantity"] = min(new_quantity, 99)  # Max limit
            await self.repo.update_cart(from_number, cart)
        
        # Show updated cart
        await self.show_cart(from_number, session)

    async def show_cart(self, from_number: str, session):
        """Display cart contents with quantity controls"""
        
        cart = await self.repo.get_cart(from_number)
        
        if not cart:
            await self.whatsapp.send_message(
                to=from_number,
                message="🛒 Your cart is empty. Start shopping to add items!"
            )
            await self.show_products(from_number)
            return
        
        # If cart has only one item, show detailed view with controls
        if len(cart) == 1:
            await self.show_cart_item_details(from_number, cart[0], session)
            return
        
        # For multiple items, show cart summary with item selection
        total = sum(float(item["price"]) * item["quantity"] for item in cart)
        
        # Create sections for list message to select items
        sections = [{
            "title": "Cart Items",
            "rows": []
        }]
        
        for item in cart:
            item_total = float(item["price"]) * item["quantity"]
            sections[0]["rows"].append({
                "id": f"cart_item_{item['product_id']}",
                "title": f"{item['title']} (×{item['quantity']})",
                "description": f"${item_total:.2f}"
            })
        
        cart_text = f"🛒 *Your Cart ({len(cart)} items):*\n\n"
        cart_text += f"💰 *Total: ${total:.2f}*\n\n"
        cart_text += "Select an item to adjust quantity:"
        
        await self.whatsapp.send_list_message(
            to=from_number,
            text=cart_text,
            button_text="Manage Items",
            sections=sections
        )
        
        # Send action buttons separately
        buttons = [
            {"id": "checkout", "title": "💳 Checkout"},
            {"id": "browse_products", "title": "🛍️ Add More"},
            {"id": "clear_cart", "title": "🗑️ Clear Cart"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text="Choose an action:",
            buttons=buttons
        )

    async def show_cart_item_details(self, from_number: str, cart_item: dict, session):
        """Show detailed view of a cart item with quantity controls"""
        
        item_total = float(cart_item["price"]) * cart_item["quantity"]
        
        text = f"🛍️ *{cart_item['title']}*\n\n"
        text += f"💰 Price: ${cart_item['price']} each\n"
        text += f"📦 Quantity: {cart_item['quantity']}\n"
        text += f"💵 Subtotal: ${item_total:.2f}"
        
        buttons = [
            {"id": f"cart_qty_decrease_{cart_item['product_id']}", "title": "➖ Remove 1"},
            {"id": f"cart_qty_increase_{cart_item['product_id']}", "title": "➕ Add 1"},
            {"id": "view_cart", "title": "🛒 Back to Cart"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text=text,
            buttons=buttons
        )

    async def start_checkout(self, from_number: str, session):
        """Start checkout process"""
        
        cart = await self.repo.get_cart(from_number)
        
        if not cart:
            await self.whatsapp.send_message(
                to=from_number,
                message="Your cart is empty. Add some products first!"
            )
            return
        
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
        
        try:
            # Create Shopify checkout
            checkout_url = await self.shopify.create_checkout(valid_items)
            
            if checkout_url:
                await self.whatsapp.send_message(
                    to=from_number,
                    message=f"🎉 Your checkout is ready!\n\nClick this link to complete your purchase:\n{checkout_url}\n\nThank you for shopping with us!"
                )
                
                # Clear cart after checkout
                await self.repo.update_cart(from_number, [])
            else:
                await self.whatsapp.send_message(
                    to=from_number,
                    message="Sorry, there was an error creating your checkout. Please try again or contact support."
                )
        except Exception as e:
            print(f"[ERROR] Checkout creation failed: {str(e)}")
            await self.whatsapp.send_message(
                to=from_number,
                message="Sorry, there was an error processing your checkout. Our team has been notified. Please try again later."
            )

    async def clear_cart(self, from_number: str, session):
        """Clear the shopping cart"""
        
        await self.repo.update_cart(from_number, [])
        
        buttons = [
            {"id": "browse_products", "title": "🛍️ Start Shopping"},
            {"id": "help", "title": "❓ Help"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text="🗑️ Your cart has been cleared.",
            buttons=buttons
        )

    async def send_help_message(self, from_number: str):
        """Send help information"""
        
        help_text = """ℹ️ *How to use this bot:*

• Send 'Hi' to start
• Browse our product catalog
• Add items to your cart
• Checkout when ready

*Commands:*
• 'cart' - View your cart
• 'help' - Show this message
• 'checkout' - Start checkout

Need assistance? Contact our support team!"""
        
        buttons = [
            {"id": "browse_products", "title": "🛍️ Start Shopping"},
            {"id": "view_cart", "title": "🛒 View Cart"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text=help_text,
            buttons=buttons
        )