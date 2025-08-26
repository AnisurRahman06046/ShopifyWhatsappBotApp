import httpx
from typing import List, Dict, Any
from app.core.config import settings


class WhatsAppService:
    def __init__(self, store_config, billing_service=None):
        self.token = store_config.whatsapp_token
        self.phone_number_id = store_config.whatsapp_phone_number_id
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        self.store = store_config
        self.billing_service = billing_service

    async def send_message(self, to: str, message: str):
        """Send a simple text message with usage tracking"""
        
        # Check usage limits before sending
        if self.billing_service:
            usage_check = await self.billing_service.check_usage_limit(self.store.id)
            if usage_check.get("limit_reached", False):
                print(f"[WARNING] Message limit reached for store {self.store.store_url}")
                return {"error": "message_limit_reached", "usage": usage_check}
        
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
            result = response.json()
            
            # Record outgoing message usage if successful
            if response.status_code == 200 and self.billing_service:
                await self.billing_service.record_usage(
                    store_id=self.store.id,
                    record_type="message_sent",
                    quantity=1,
                    phone_number=to,
                    message_type="text",
                    description="Outgoing text message"
                )
            
            return result

    async def send_button_message(self, to: str, text: str, buttons: List[Dict[str, str]]):
        """Send an interactive button message with usage tracking"""
        
        # Check usage limits before sending
        if self.billing_service:
            usage_check = await self.billing_service.check_usage_limit(self.store.id)
            if usage_check.get("limit_reached", False):
                print(f"[WARNING] Message limit reached for store {self.store.store_url}")
                return {"error": "message_limit_reached", "usage": usage_check}
        
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
            result = response.json()
            
            # Record outgoing message usage if successful
            if response.status_code == 200 and self.billing_service:
                await self.billing_service.record_usage(
                    store_id=self.store.id,
                    record_type="message_sent",
                    quantity=1,
                    phone_number=to,
                    message_type="interactive_button",
                    description="Outgoing button message"
                )
            
            return result

    async def send_list_message(self, to: str, text: str, button_text: str, sections: List[Dict]):
        """Send an interactive list message with usage tracking"""
        
        # Check usage limits before sending
        if self.billing_service:
            usage_check = await self.billing_service.check_usage_limit(self.store.id)
            if usage_check.get("limit_reached", False):
                print(f"[WARNING] Message limit reached for store {self.store.store_url}")
                return {"error": "message_limit_reached", "usage": usage_check}
        
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
            result = response.json()
            
            # Record outgoing message usage if successful
            if response.status_code == 200 and self.billing_service:
                await self.billing_service.record_usage(
                    store_id=self.store.id,
                    record_type="message_sent",
                    quantity=1,
                    phone_number=to,
                    message_type="interactive_list",
                    description="Outgoing list message"
                )
            
            return result

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


# ShopifyService class removed - REST API calls migrated to GraphQL via ShopifyAPIAdapter
# Use ShopifyAPIAdapter with use_graphql=True instead for all Shopify operations