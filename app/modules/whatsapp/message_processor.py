import json
from typing import Dict, List, Any


class MessageProcessor:
    def __init__(self, whatsapp_service, shopify_service, whatsapp_repo, store):
        self.whatsapp = whatsapp_service
        self.shopify = shopify_service
        self.repo = whatsapp_repo
        self.store = store

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
            product_id = button_id.replace("add_to_cart_", "")
            await self.add_to_cart(from_number, product_id, session)
        
        elif button_id.startswith("view_product_"):
            product_id = button_id.replace("view_product_", "")
            await self.show_product_details(from_number, product_id)
        
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

    async def show_products(self, from_number: str):
        """Display product catalog"""
        
        products = await self.shopify.get_products(limit=10)
        
        if not products:
            await self.whatsapp.send_message(
                to=from_number,
                message="Sorry, no products available at the moment."
            )
            return
        
        # Create sections for list message
        sections = [{
            "title": "Available Products",
            "rows": []
        }]
        
        for product in products[:10]:  # WhatsApp limit
            sections[0]["rows"].append({
                "id": f"product_{product['id']}",
                "title": product["title"][:24],  # WhatsApp limit
                "description": f"${product['price']}"
            })
        
        await self.whatsapp.send_list_message(
            to=from_number,
            text="📦 Here are our available products:",
            button_text="View Products",
            sections=sections
        )

    async def show_product_details(self, from_number: str, product_id: str):
        """Show detailed product information"""
        
        product = await self.shopify.get_product(product_id)
        
        if not product:
            await self.whatsapp.send_message(
                to=from_number,
                message="Sorry, product not found."
            )
            return
        
        await self.whatsapp.send_product_message(from_number, product)

    async def add_to_cart(self, from_number: str, product_id: str, session):
        """Add product to cart"""
        
        # Get current cart
        cart = await self.repo.get_cart(from_number)
        
        # Get product details
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
            "quantity": 1
        }
        
        # Check if product already in cart
        existing_item = next((item for item in cart if item["product_id"] == product_id), None)
        
        if existing_item:
            existing_item["quantity"] += 1
        else:
            cart.append(cart_item)
        
        # Update cart in database
        await self.repo.update_cart(from_number, cart)
        
        # Send confirmation
        buttons = [
            {"id": "view_cart", "title": "🛒 View Cart"},
            {"id": "browse_products", "title": "🛍️ Continue Shopping"},
            {"id": "checkout", "title": "💳 Checkout"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text=f"✅ Added '{product['title']}' to your cart!",
            buttons=buttons
        )

    async def show_cart(self, from_number: str, session):
        """Display cart contents"""
        
        cart = await self.repo.get_cart(from_number)
        
        if not cart:
            await self.whatsapp.send_message(
                to=from_number,
                message="🛒 Your cart is empty. Start shopping to add items!"
            )
            await self.show_products(from_number)
            return
        
        # Calculate total
        total = sum(float(item["price"]) * item["quantity"] for item in cart)
        
        # Build cart message
        cart_text = "🛒 *Your Cart:*\n\n"
        for item in cart:
            cart_text += f"• {item['title']}\n"
            cart_text += f"  Qty: {item['quantity']} × ${item['price']}\n\n"
        
        cart_text += f"*Total: ${total:.2f}*"
        
        buttons = [
            {"id": "checkout", "title": "💳 Checkout"},
            {"id": "browse_products", "title": "🛍️ Add More"},
            {"id": "clear_cart", "title": "🗑️ Clear Cart"}
        ]
        
        await self.whatsapp.send_button_message(
            to=from_number,
            text=cart_text,
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