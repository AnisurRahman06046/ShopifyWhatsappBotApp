import httpx
import json
from typing import List, Dict, Any
from app.core.config import settings


class WhatsAppService:
    def __init__(self, store_config):
        self.token = store_config.whatsapp_token
        self.phone_number_id = store_config.whatsapp_phone_number_id
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"

    async def send_message(self, to: str, message: str):
        """Send a simple text message"""
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            return response.json()

    async def send_button_message(self, to: str, text: str, buttons: List[Dict[str, str]]):
        """Send an interactive button message"""
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        interactive_buttons = []
        for i, button in enumerate(buttons):
            interactive_buttons.append({
                "type": "reply",
                "reply": {
                    "id": button["id"],
                    "title": button["title"]
                }
            })
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {
                    "buttons": interactive_buttons
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            return response.json()

    async def send_list_message(self, to: str, text: str, button_text: str, sections: List[Dict]):
        """Send an interactive list message"""
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": text},
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            return response.json()

    async def send_product_message(self, to: str, product: Dict[str, Any], quantity: int = 1):
        """Send a product message with quantity controls"""
        text = f"🛍️ *{product['title']}*\n\n"
        text += f"💰 Price: ${product['price']}\n"
        if product.get('description'):
            text += f"📝 {product['description'][:200]}...\n"
        
        text += f"\n📦 Quantity: {quantity}\n"
        text += f"💵 Total: ${float(product['price']) * quantity:.2f}"
        
        buttons = [
            {"id": f"qty_decrease_{product['id']}_{quantity}", "title": "➖ Less"},
            {"id": f"qty_increase_{product['id']}_{quantity}", "title": "➕ More"},
            {"id": f"add_to_cart_{product['id']}_{quantity}", "title": f"🛒 Add {quantity} to Cart"}
        ]
        
        await self.send_button_message(to, text, buttons)


class ShopifyService:
    def __init__(self, store_url: str, access_token: str):
        self.store_url = store_url
        self.access_token = access_token
        self.base_url = f"https://{store_url}/admin/api/2024-01"

    async def get_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch products from Shopify store"""
        url = f"{self.base_url}/products.json?limit={limit}"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        print(f"[DEBUG] Shopify URL: {url}")
        print(f"[DEBUG] Access Token: {self.access_token[:15]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            print(f"[DEBUG] Shopify Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[DEBUG] Products found: {len(data.get('products', []))}")
                
                products = []
                for product in data.get("products", []):
                    print(f"[DEBUG] Processing product: {product.get('title', 'No Title')}")
                    
                    variant = product["variants"][0] if product["variants"] else {}
                    
                    # Safe description handling with HTML tag removal
                    description = product.get("body_html")
                    print(f"[DEBUG] Raw description: {type(description)} - {description}")
                    
                    if description is None:
                        description = ""
                    else:
                        # Remove common HTML tags
                        import re
                        description = str(description)
                        description = re.sub(r'<[^>]+>', '', description)  # Remove all HTML tags
                        description = description.replace("&nbsp;", " ").strip()  # Clean up entities
                    
                    products.append({
                        "id": product["id"],
                        "title": product["title"],
                        "description": description,
                        "price": variant.get("price", "0"),
                        "image": product["images"][0]["src"] if product["images"] else None,
                        "variant_id": variant.get("id")
                    })
                return products
            else:
                print(f"[DEBUG] Shopify API Error: {response.text}")
                return []

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a specific product by ID"""
        url = f"{self.base_url}/products/{product_id}.json"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                product = response.json()["product"]
                variant = product["variants"][0] if product["variants"] else {}
                
                # Clean description
                description = product.get("body_html")
                if description is None:
                    description = ""
                else:
                    import re
                    description = str(description)
                    description = re.sub(r'<[^>]+>', '', description)  # Remove all HTML tags
                    description = description.replace("&nbsp;", " ").strip()
                
                return {
                    "id": product["id"],
                    "title": product["title"],
                    "description": description,
                    "price": variant.get("price", "0"),
                    "image": product["images"][0]["src"] if product["images"] else None,
                    "variant_id": variant.get("id")
                }
            return {}

    async def create_checkout(self, line_items: List[Dict]) -> str:
        """Create checkout using multiple methods"""
        
        # Method 1: Try creating a permalink cart URL
        cart_url = await self.create_cart_permalink(line_items)
        if cart_url:
            return cart_url
        
        # Method 2: Fallback to draft order
        return await self.create_draft_order_checkout(line_items)
    
    async def create_cart_permalink(self, line_items: List[Dict]) -> str:
        """Create a cart permalink URL for checkout"""
        try:
            # Build cart URL with variant IDs and quantities
            cart_params = []
            for item in line_items:
                cart_params.append(f"{item['variant_id']}:{item['quantity']}")
            
            # Create cart URL
            cart_string = ",".join(cart_params)
            checkout_url = f"https://{self.store_url}/cart/{cart_string}"
            
            print(f"[DEBUG] Created cart permalink: {checkout_url}")
            return checkout_url
        except Exception as e:
            print(f"[ERROR] Failed to create cart permalink: {str(e)}")
            return ""
    
    async def create_draft_order_checkout(self, line_items: List[Dict]) -> str:
        """Create a draft order and get checkout URL"""
        url = f"{self.base_url}/draft_orders.json"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        # Transform line items to draft order format
        draft_line_items = []
        for item in line_items:
            draft_line_items.append({
                "variant_id": item["variant_id"],
                "quantity": item["quantity"]
            })
        
        data = {
            "draft_order": {
                "line_items": draft_line_items,
                "note": "Order from WhatsApp Bot",
                "use_customer_default_address": True
            }
        }
        
        print(f"[DEBUG] Creating draft order with data: {json.dumps(data)}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                print(f"[DEBUG] Draft order response status: {response.status_code}")
                
                if response.status_code == 201:
                    draft_order = response.json()["draft_order"]
                    
                    # Get the invoice URL
                    invoice_url = draft_order.get("invoice_url")
                    
                    if not invoice_url and draft_order.get("invoice_token"):
                        # Construct the invoice URL manually
                        invoice_url = f"https://{self.store_url}/draft_orders/{draft_order['invoice_token']}"
                    
                    if invoice_url:
                        print(f"[DEBUG] Generated draft order URL: {invoice_url}")
                        return invoice_url
                    else:
                        # Fallback: Create a cart URL with the draft order items
                        cart_params = []
                        for item in draft_order.get("line_items", []):
                            if item.get("variant_id"):
                                cart_params.append(f"{item['variant_id']}:{item['quantity']}")
                        
                        if cart_params:
                            cart_string = ",".join(cart_params)
                            checkout_url = f"https://{self.store_url}/cart/{cart_string}"
                            print(f"[DEBUG] Fallback to cart URL: {checkout_url}")
                            return checkout_url
                else:
                    print(f"[ERROR] Failed to create draft order: {response.text}")
                    
                    # Fallback to cart URL even on draft order failure
                    cart_params = []
                    for item in line_items:
                        cart_params.append(f"{item['variant_id']}:{item['quantity']}")
                    
                    if cart_params:
                        cart_string = ",".join(cart_params)
                        checkout_url = f"https://{self.store_url}/cart/{cart_string}"
                        print(f"[DEBUG] Fallback to cart URL after error: {checkout_url}")
                        return checkout_url
        except Exception as e:
            print(f"[ERROR] Exception in create_draft_order_checkout: {str(e)}")
            
            # Last resort: Return a cart URL
            try:
                cart_params = []
                for item in line_items:
                    cart_params.append(f"{item['variant_id']}:{item['quantity']}")
                
                if cart_params:
                    cart_string = ",".join(cart_params)
                    checkout_url = f"https://{self.store_url}/cart/{cart_string}"
                    print(f"[DEBUG] Last resort cart URL: {checkout_url}")
                    return checkout_url
            except:
                pass
        
        return ""