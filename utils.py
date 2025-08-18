

import requests


def send_dynamic_whatsapp_message(recipient_number: str, message_text: str, shop):
    url = f"https://graph.facebook.com/v19.0/{shop.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {shop.access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message_text},
    }
    return requests.post(url, json=payload, headers=headers)


def send_dynamic_buttons(recipient_number: str, shop):
    url = f"https://graph.facebook.com/v19.0/{shop.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {shop.access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "👋 Welcome to WhatsApp Shop!\nPlease choose an option:"},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "browse_products",
                            "title": "🛍 Browse Products",
                        },
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "view_cart", "title": "🛒 View Cart"},
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "place_order", "title": "📦 Place Order"},
                    },
                ]
            },
        },
    }
    return requests.post(url, json=payload, headers=headers)



def send_dynamic_product_list(recipient_number: str, shop, products: list[dict]):
    url = f"https://graph.facebook.com/v19.0/{shop.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {shop.access_token}",
        "Content-Type": "application/json",
    }

    rows = []
    for product in products[:10]:  # Limit to first 10 for WhatsApp list cap
        rows.append(
            {
                "id": str(product.get("id", "unknown")),
                "title": product.get("name", "Unnamed Product"),
                "description": f"{product.get('price', 'N/A')} - {product.get('short_description', '')[:50]}",
            }
        )

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🛍 Product Catalog"},
            "body": {"text": "Please select a product to view details:"},
            "footer": {"text": "Tap a product below"},
            "action": {
                "button": "View Products",
                "sections": [
                    {
                        "title": "Available Products",
                        "rows": rows,
                    }
                ],
            },
        },
    }

    return requests.post(url, json=payload, headers=headers)
