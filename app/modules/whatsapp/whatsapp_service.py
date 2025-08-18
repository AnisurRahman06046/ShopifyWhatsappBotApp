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

    async def send_product_message(self, to: str, product: Dict[str, Any]):
        """Send a product message with image and details"""
        text = f"🛍️ *{product['title']}*\n\n"
        text += f"💰 Price: ${product['price']}\n"
        if product.get('description'):
            text += f"📝 {product['description'][:200]}..."
        
        buttons = [
            {"id": f"add_to_cart_{product['id']}", "title": "🛒 Add to Cart"},
            {"id": "browse_more", "title": "👀 Browse More"}
        ]
        
        await self.send_button_message(to, text, buttons)


class ShopifyService:
    def __init__(self, store_url: str, access_token: str):
        self.store_url = store_url
        self.access_token = access_token
        self.base_url = f"https://{store_url}/admin/api/2023-10"

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
        """Create a checkout session for cart items"""
        url = f"{self.base_url}/checkouts.json"
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
        
        data = {
            "checkout": {
                "line_items": line_items
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 201:
                checkout = response.json()["checkout"]
                return checkout["web_url"]
            return ""