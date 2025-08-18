# engine.py
from data import categories

def show_main_menu():
    return {
        "text": "🤖 Welcome to SmartShop!",
        "buttons": [
            {"title": "🛍 Shop Products", "payload": "shop_products"},
            {"title": "❓ Track Order", "payload": "track_order"},
            {"title": "🔧 Support", "payload": "support"},
        ]
    }

def show_categories():
    return {
        "text": "Select a category:",
        "buttons": [
            {"title": "🎧 Headphones", "payload": "cat_headphones"},
            {"title": "⌚ Smartwatches", "payload": "cat_watches"}
        ]
    }

def show_products(category_key):
    items = categories[category_key]
    return [
        {"title": f"{item['name']} - ${item['price']}", "payload": f"product_{item['id']}"}
        for item in items
    ]

def get_product_by_id(category_key, product_id):
    for item in categories[category_key]:
        if item['id'] == product_id:
            return item
    return None
