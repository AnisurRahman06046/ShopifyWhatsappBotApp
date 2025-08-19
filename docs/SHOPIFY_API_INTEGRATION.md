# Shopify API Integration Documentation

## Overview

This document provides comprehensive coverage of Shopify API integration used in the WhatsApp bot, including REST API and GraphQL API structures, product fetching, order creation, and complete API references.

## Table of Contents

1. [API Authentication](#api-authentication)
2. [Product Management APIs](#product-management-apis)
3. [Order Management APIs](#order-management-apis)
4. [Draft Orders API](#draft-orders-api)
5. [Checkout & Cart APIs](#checkout--cart-apis)
6. [API Version Management](#api-version-management)
7. [Error Handling](#error-handling)
8. [GraphQL vs REST](#graphql-vs-rest)
9. [Implementation Examples](#implementation-examples)
10. [Testing & Debugging](#testing--debugging)

---

## API Authentication

### Access Token Setup

Shopify uses OAuth 2.0 for API authentication with access tokens.

```python
# Authentication Headers
headers = {
    "X-Shopify-Access-Token": "shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "Content-Type": "application/json"
}

# Store URL Format
store_url = "your-store.myshopify.com"
base_url = f"https://{store_url}/admin/api/2024-01"
```

### Required Scopes

```javascript
// App installation scopes
const scopes = [
    "read_products",           // Read products
    "write_products",          // Modify products
    "read_orders",             // Read orders
    "write_orders",            // Create/modify orders
    "write_draft_orders",      // Create draft orders
    "read_customers",          // Read customer data
    "write_customers",         // Create customers
    "read_inventory",          // Check stock levels
    "write_inventory"          // Update inventory
];
```

---

## Product Management APIs

### 1. Fetch Products (REST API)

#### Basic Product Retrieval

```python
# GET /admin/api/2024-01/products.json
async def get_products(self, limit: int = 10, page: int = 1) -> List[Dict[str, Any]]:
    """Fetch products from Shopify store"""
    
    params = {
        "limit": limit,
        "page": page,
        "status": "active",
        "published_status": "published"
    }
    
    url = f"{self.base_url}/products.json"
    response = await client.get(url, headers=headers, params=params)
    
    return response.json()
```

#### API Response Structure

```json
{
  "products": [
    {
      "id": 8394948493462,
      "title": "Premium T-Shirt",
      "body_html": "<p>High-quality cotton t-shirt</p>",
      "vendor": "Your Store",
      "product_type": "Clothing",
      "created_at": "2024-01-15T10:30:00-05:00",
      "updated_at": "2024-01-15T10:30:00-05:00",
      "published_at": "2024-01-15T10:30:00-05:00",
      "template_suffix": null,
      "published_scope": "web",
      "tags": "cotton, premium, clothing",
      "status": "active",
      "admin_graphql_api_id": "gid://shopify/Product/8394948493462",
      "variants": [
        {
          "id": 45158423330966,
          "product_id": 8394948493462,
          "title": "Default Title",
          "price": "25.00",
          "sku": "PREM-TSHIRT-001",
          "position": 1,
          "inventory_policy": "deny",
          "compare_at_price": "30.00",
          "fulfillment_service": "manual",
          "inventory_management": "shopify",
          "option1": "Default Title",
          "option2": null,
          "option3": null,
          "created_at": "2024-01-15T10:30:00-05:00",
          "updated_at": "2024-01-15T10:30:00-05:00",
          "taxable": true,
          "barcode": null,
          "grams": 200,
          "image_id": null,
          "weight": 0.2,
          "weight_unit": "kg",
          "inventory_item_id": 47079973109910,
          "inventory_quantity": 100,
          "old_inventory_quantity": 100,
          "requires_shipping": true,
          "admin_graphql_api_id": "gid://shopify/ProductVariant/45158423330966"
        }
      ],
      "options": [
        {
          "id": 10984802050198,
          "product_id": 8394948493462,
          "name": "Title",
          "position": 1,
          "values": ["Default Title"]
        }
      ],
      "images": [
        {
          "id": 37164683559062,
          "alt": null,
          "position": 1,
          "product_id": 8394948493462,
          "created_at": "2024-01-15T10:30:00-05:00",
          "updated_at": "2024-01-15T10:30:00-05:00",
          "admin_graphql_api_id": "gid://shopify/ProductImage/37164683559062",
          "width": 1200,
          "height": 1200,
          "src": "https://cdn.shopify.com/s/files/1/0000/0000/0000/products/tshirt.jpg?v=1705330200",
          "variant_ids": []
        }
      ],
      "image": {
        "id": 37164683559062,
        "alt": null,
        "position": 1,
        "product_id": 8394948493462,
        "created_at": "2024-01-15T10:30:00-05:00",
        "updated_at": "2024-01-15T10:30:00-05:00",
        "admin_graphql_api_id": "gid://shopify/ProductImage/37164683559062",
        "width": 1200,
        "height": 1200,
        "src": "https://cdn.shopify.com/s/files/1/0000/0000/0000/products/tshirt.jpg?v=1705330200",
        "variant_ids": []
      }
    }
  ]
}
```

### 2. Fetch Single Product

```python
# GET /admin/api/2024-01/products/{product_id}.json
async def get_product(self, product_id: str) -> Dict[str, Any]:
    """Get a specific product by ID"""
    
    url = f"{self.base_url}/products/{product_id}.json"
    response = await client.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()["product"]
    return {}
```

### 3. Product Filtering & Search

```python
# Advanced product filtering
params = {
    "limit": 50,
    "vendor": "Your Brand",
    "product_type": "Clothing",
    "collection_id": 123456789,
    "created_at_min": "2024-01-01T00:00:00-05:00",
    "created_at_max": "2024-12-31T23:59:59-05:00",
    "updated_at_min": "2024-01-01T00:00:00-05:00",
    "handle": "premium-t-shirt",
    "ids": "8394948493462,8394948493463",
    "published_status": "published",
    "status": "active",
    "title": "Premium",
    "fields": "id,title,handle,product_type,vendor,variants"
}
```

### 4. GraphQL Product Query

```graphql
query getProducts($first: Int!, $query: String) {
  products(first: $first, query: $query) {
    edges {
      node {
        id
        title
        handle
        description
        productType
        vendor
        tags
        createdAt
        updatedAt
        status
        totalInventory
        variants(first: 10) {
          edges {
            node {
              id
              title
              price
              compareAtPrice
              sku
              inventoryQuantity
              availableForSale
              weight
              weightUnit
              image {
                id
                url
                altText
              }
            }
          }
        }
        images(first: 5) {
          edges {
            node {
              id
              url
              altText
              width
              height
            }
          }
        }
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
          maxVariantPrice {
            amount
            currencyCode
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
```

---

## Order Management APIs

### 1. Fetch Orders (REST API)

```python
# GET /admin/api/2024-01/orders.json
async def get_orders(self, status: str = "any", limit: int = 50) -> List[Dict]:
    """Fetch orders from store"""
    
    params = {
        "status": status,  # any, open, closed, cancelled
        "limit": limit,
        "financial_status": "paid",  # pending, authorized, paid, refunded
        "fulfillment_status": "unfulfilled"  # fulfilled, partial, unfulfilled
    }
    
    url = f"{self.base_url}/orders.json"
    response = await client.get(url, headers=headers, params=params)
    
    return response.json()["orders"]
```

#### Order Response Structure

```json
{
  "orders": [
    {
      "id": 5479469146262,
      "admin_graphql_api_id": "gid://shopify/Order/5479469146262",
      "app_id": 580111,
      "browser_ip": "192.168.1.1",
      "buyer_accepts_marketing": false,
      "cancel_reason": null,
      "cancelled_at": null,
      "cart_token": "c1-1234567890abcdef",
      "checkout_id": 33665333084326,
      "checkout_token": "abcdef1234567890",
      "client_details": {
        "accept_language": "en-US,en;q=0.9",
        "browser_height": 1080,
        "browser_ip": "192.168.1.1",
        "browser_width": 1920,
        "session_hash": null,
        "user_agent": "Mozilla/5.0..."
      },
      "closed_at": null,
      "confirmed": true,
      "contact_email": "customer@example.com",
      "created_at": "2024-08-19T10:30:00-04:00",
      "currency": "USD",
      "current_subtotal_price": "25.00",
      "current_subtotal_price_set": {
        "shop_money": {
          "amount": "25.00",
          "currency_code": "USD"
        },
        "presentment_money": {
          "amount": "25.00",
          "currency_code": "USD"
        }
      },
      "current_total_discounts": "0.00",
      "current_total_price": "27.50",
      "current_total_tax": "2.50",
      "customer_locale": "en",
      "device_id": null,
      "discount_codes": [],
      "financial_status": "paid",
      "fulfillment_status": null,
      "gateway": "stripe",
      "landing_site": "/products/premium-t-shirt",
      "landing_site_ref": null,
      "location_id": null,
      "name": "#1001",
      "note": "Order from WhatsApp Bot",
      "note_attributes": [
        {
          "name": "Source",
          "value": "WhatsApp Bot"
        }
      ],
      "number": 1001,
      "order_number": 1001,
      "order_status_url": "https://your-store.myshopify.com/12345/orders/abcdef/authenticate?key=xyz",
      "original_total_duties_set": null,
      "payment_gateway_names": ["stripe"],
      "phone": "+1234567890",
      "presentment_currency": "USD",
      "processed_at": "2024-08-19T10:30:00-04:00",
      "processing_method": "direct",
      "reference": null,
      "referring_site": "",
      "source_identifier": null,
      "source_name": "web",
      "source_url": null,
      "subtotal_price": "25.00",
      "tags": "whatsapp-bot",
      "tax_lines": [
        {
          "price": "2.50",
          "rate": 0.1,
          "title": "VAT",
          "price_set": {
            "shop_money": {
              "amount": "2.50",
              "currency_code": "USD"
            },
            "presentment_money": {
              "amount": "2.50",
              "currency_code": "USD"
            }
          }
        }
      ],
      "taxes_included": false,
      "test": false,
      "token": "abcdef1234567890",
      "total_discounts": "0.00",
      "total_line_items_price": "25.00",
      "total_outstanding": "0.00",
      "total_price": "27.50",
      "total_price_usd": "27.50",
      "total_shipping_price_set": {
        "shop_money": {
          "amount": "0.00",
          "currency_code": "USD"
        },
        "presentment_money": {
          "amount": "0.00",
          "currency_code": "USD"
        }
      },
      "total_tax": "2.50",
      "total_tip_received": "0.00",
      "total_weight": 200,
      "updated_at": "2024-08-19T10:30:00-04:00",
      "user_id": null,
      "billing_address": {
        "first_name": "John",
        "address1": "123 Main St",
        "phone": "+1234567890",
        "city": "New York",
        "zip": "10001",
        "province": "New York",
        "country": "United States",
        "last_name": "Doe",
        "address2": "Apt 4B",
        "company": null,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "name": "John Doe",
        "country_code": "US",
        "province_code": "NY"
      },
      "customer": {
        "id": 6855515070614,
        "email": "customer@example.com",
        "accepts_marketing": false,
        "created_at": "2024-08-19T10:30:00-04:00",
        "updated_at": "2024-08-19T10:30:00-04:00",
        "first_name": "John",
        "last_name": "Doe",
        "orders_count": 1,
        "state": "enabled",
        "total_spent": "27.50",
        "last_order_id": 5479469146262,
        "note": null,
        "verified_email": true,
        "multipass_identifier": null,
        "tax_exempt": false,
        "phone": "+1234567890",
        "tags": "whatsapp-customer",
        "last_order_name": "#1001",
        "currency": "USD",
        "addresses": [],
        "accepts_marketing_updated_at": "2024-08-19T10:30:00-04:00",
        "marketing_opt_in_level": "single_opt_in",
        "tax_exemptions": [],
        "email_marketing_consent": null,
        "sms_marketing_consent": null,
        "admin_graphql_api_id": "gid://shopify/Customer/6855515070614",
        "default_address": null
      },
      "discount_applications": [],
      "fulfillments": [],
      "line_items": [
        {
          "id": 13488699072662,
          "admin_graphql_api_id": "gid://shopify/LineItem/13488699072662",
          "fulfillable_quantity": 1,
          "fulfillment_service": "manual",
          "fulfillment_status": null,
          "gift_card": false,
          "grams": 200,
          "name": "Premium T-Shirt",
          "origin_location": {
            "id": 3832426332310,
            "country_code": "US",
            "province_code": "NY",
            "name": "Your Store",
            "address1": "123 Store St",
            "address2": "",
            "city": "New York",
            "zip": "10001"
          },
          "price": "25.00",
          "price_set": {
            "shop_money": {
              "amount": "25.00",
              "currency_code": "USD"
            },
            "presentment_money": {
              "amount": "25.00",
              "currency_code": "USD"
            }
          },
          "product_exists": true,
          "product_id": 8394948493462,
          "properties": [],
          "quantity": 1,
          "requires_shipping": true,
          "sku": "PREM-TSHIRT-001",
          "taxable": true,
          "title": "Premium T-Shirt",
          "total_discount": "0.00",
          "total_discount_set": {
            "shop_money": {
              "amount": "0.00",
              "currency_code": "USD"
            },
            "presentment_money": {
              "amount": "0.00",
              "currency_code": "USD"
            }
          },
          "variant_id": 45158423330966,
          "variant_inventory_management": "shopify",
          "variant_title": "Default Title",
          "vendor": "Your Store",
          "tax_lines": [
            {
              "channel_liable": null,
              "price": "2.50",
              "price_set": {
                "shop_money": {
                  "amount": "2.50",
                  "currency_code": "USD"
                },
                "presentment_money": {
                  "amount": "2.50",
                  "currency_code": "USD"
                }
              },
              "rate": 0.1,
              "title": "VAT"
            }
          ],
          "duties": [],
          "discount_allocations": []
        }
      ],
      "payment_details": {
        "credit_card_bin": null,
        "avs_result_code": null,
        "cvv_result_code": null,
        "credit_card_number": "•••• •••• •••• 4242",
        "credit_card_company": "Visa"
      },
      "refunds": [],
      "shipping_address": {
        "first_name": "John",
        "address1": "123 Main St",
        "phone": "+1234567890",
        "city": "New York",
        "zip": "10001",
        "province": "New York",
        "country": "United States",
        "last_name": "Doe",
        "address2": "Apt 4B",
        "company": null,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "name": "John Doe",
        "country_code": "US",
        "province_code": "NY"
      },
      "shipping_lines": []
    }
  ]
}
```

### 2. Create Order (REST API)

```python
# POST /admin/api/2024-01/orders.json
async def create_order(self, order_data: Dict) -> Dict:
    """Create a new order"""
    
    order_payload = {
        "order": {
            "line_items": [
                {
                    "variant_id": 45158423330966,
                    "quantity": 2,
                    "price": "25.00"
                }
            ],
            "customer": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "customer@example.com",
                "phone": "+1234567890"
            },
            "billing_address": {
                "first_name": "John",
                "last_name": "Doe",
                "address1": "123 Main St",
                "city": "New York",
                "province": "NY",
                "country": "US",
                "zip": "10001",
                "phone": "+1234567890"
            },
            "shipping_address": {
                "first_name": "John",
                "last_name": "Doe",
                "address1": "123 Main St",
                "city": "New York",
                "province": "NY",
                "country": "US",
                "zip": "10001",
                "phone": "+1234567890"
            },
            "financial_status": "pending",
            "fulfillment_status": "unfulfilled",
            "send_receipt": True,
            "send_fulfillment_receipt": True,
            "note": "Order created via WhatsApp Bot",
            "tags": "whatsapp-bot, automated",
            "note_attributes": [
                {
                    "name": "Source",
                    "value": "WhatsApp Bot"
                },
                {
                    "name": "Channel",
                    "value": "WhatsApp"
                }
            ]
        }
    }
    
    url = f"{self.base_url}/orders.json"
    response = await client.post(url, headers=headers, json=order_payload)
    
    return response.json()
```

---

## Draft Orders API

### 1. Create Draft Order

```python
# POST /admin/api/2024-01/draft_orders.json
async def create_draft_order(self, line_items: List[Dict]) -> str:
    """Create a draft order and get checkout URL"""
    
    draft_order_payload = {
        "draft_order": {
            "line_items": [
                {
                    "variant_id": item["variant_id"],
                    "quantity": item["quantity"],
                    "applied_discount": {
                        "description": "WhatsApp Customer Discount",
                        "value_type": "percentage",
                        "value": "5.0",
                        "amount": "1.25",
                        "title": "5% WhatsApp Discount"
                    }
                }
                for item in line_items
            ],
            "customer": {
                "id": 6855515070614  # Existing customer ID
            },
            "shipping_address": {
                "first_name": "John",
                "last_name": "Doe",
                "address1": "123 Main St",
                "city": "New York",
                "province": "NY",
                "country": "US",
                "zip": "10001",
                "phone": "+1234567890"
            },
            "billing_address": {
                "first_name": "John",
                "last_name": "Doe",
                "address1": "123 Main St",
                "city": "New York",
                "province": "NY",
                "country": "US",
                "zip": "10001",
                "phone": "+1234567890"
            },
            "note": "Draft order created via WhatsApp Bot",
            "email": "customer@example.com",
            "currency": "USD",
            "invoice_sent_at": None,
            "invoice_url": None,
            "use_customer_default_address": True,
            "applied_discount": {
                "description": "WhatsApp Customer Discount",
                "value_type": "percentage", 
                "value": "10.0",
                "amount": "2.50",
                "title": "10% New Customer Discount"
            },
            "shipping_line": {
                "title": "Standard Shipping",
                "price": "5.00",
                "code": "STANDARD",
                "source": "shopify"
            },
            "tax_lines": [
                {
                    "title": "VAT",
                    "price": "2.50",
                    "rate": 0.1
                }
            ],
            "tags": "whatsapp-bot, draft-order"
        }
    }
    
    url = f"{self.base_url}/draft_orders.json"
    response = await client.post(url, headers=headers, json=draft_order_payload)
    
    if response.status_code == 201:
        draft_order = response.json()["draft_order"]
        return draft_order.get("invoice_url") or f"https://{self.store_url}/draft_orders/{draft_order['invoice_token']}"
    
    return ""
```

#### Draft Order Response Structure

```json
{
  "draft_order": {
    "id": 1054381702,
    "note": "Draft order created via WhatsApp Bot",
    "email": "customer@example.com",
    "taxes_included": false,
    "currency": "USD",
    "invoice_sent_at": null,
    "created_at": "2024-08-19T10:30:00-04:00",
    "updated_at": "2024-08-19T10:30:00-04:00",
    "tax_exempt": false,
    "completed_at": null,
    "name": "#D1",
    "status": "open",
    "line_items": [
      {
        "id": 1071823346,
        "variant_id": 45158423330966,
        "product_id": 8394948493462,
        "title": "Premium T-Shirt",
        "variant_title": "Default Title",
        "sku": "PREM-TSHIRT-001",
        "vendor": "Your Store",
        "quantity": 2,
        "requires_shipping": true,
        "taxable": true,
        "gift_card": false,
        "fulfillment_service": "manual",
        "grams": 400,
        "tax_lines": [],
        "applied_discount": {
          "description": "WhatsApp Customer Discount",
          "value": "5.0",
          "title": "5% WhatsApp Discount",
          "amount": "2.50",
          "value_type": "percentage"
        },
        "name": "Premium T-Shirt",
        "properties": [],
        "custom": false,
        "price": "25.00",
        "admin_graphql_api_id": "gid://shopify/DraftOrderLineItem/1071823346"
      }
    ],
    "shipping_address": {
      "first_name": "John",
      "address1": "123 Main St",
      "phone": "+1234567890",
      "city": "New York",
      "zip": "10001",
      "province": "New York",
      "country": "United States",
      "last_name": "Doe",
      "address2": null,
      "company": null,
      "latitude": null,
      "longitude": null,
      "name": "John Doe",
      "country_code": "US",
      "province_code": "NY"
    },
    "billing_address": {
      "first_name": "John",
      "address1": "123 Main St",
      "phone": "+1234567890",
      "city": "New York",
      "zip": "10001",
      "province": "New York",
      "country": "United States",
      "last_name": "Doe",
      "address2": null,
      "company": null,
      "latitude": null,
      "longitude": null,
      "name": "John Doe",
      "country_code": "US",
      "province_code": "NY"
    },
    "invoice_url": "https://your-store.myshopify.com/draft_orders/abc123def456",
    "applied_discount": {
      "description": "WhatsApp Customer Discount",
      "value": "10.0",
      "title": "10% New Customer Discount",
      "amount": "5.00",
      "value_type": "percentage"
    },
    "order_id": null,
    "shipping_line": {
      "title": "Standard Shipping",
      "custom": false,
      "handle": "standard-shipping",
      "price": "5.00"
    },
    "tax_lines": [
      {
        "rate": 0.1,
        "title": "VAT",
        "price": "4.75"
      }
    ],
    "tags": "whatsapp-bot, draft-order",
    "note_attributes": [],
    "total_price": "52.25",
    "subtotal_price": "47.50",
    "total_tax": "4.75",
    "presentment_currency": "USD",
    "total_line_items_price_set": {
      "shop_money": {
        "amount": "50.00",
        "currency_code": "USD"
      },
      "presentment_money": {
        "amount": "50.00",
        "currency_code": "USD"
      }
    },
    "total_discounts_set": {
      "shop_money": {
        "amount": "7.50",
        "currency_code": "USD"
      },
      "presentment_money": {
        "amount": "7.50",
        "currency_code": "USD"
      }
    },
    "total_line_items_price": "50.00",
    "total_price_set": {
      "shop_money": {
        "amount": "52.25",
        "currency_code": "USD"
      },
      "presentment_money": {
        "amount": "52.25",
        "currency_code": "USD"
      }
    },
    "subtotal_price_set": {
      "shop_money": {
        "amount": "47.50",
        "currency_code": "USD"
      },
      "presentment_money": {
        "amount": "47.50",
        "currency_code": "USD"
      }
    },
    "total_tax_set": {
      "shop_money": {
        "amount": "4.75",
        "currency_code": "USD"
      },
      "presentment_money": {
        "amount": "4.75",
        "currency_code": "USD"
      }
    },
    "total_discounts": "7.50",
    "total_shipping_price_set": {
      "shop_money": {
        "amount": "5.00",
        "currency_code": "USD"
      },
      "presentment_money": {
        "amount": "5.00",
        "currency_code": "USD"
      }
    },
    "customer": {
      "id": 6855515070614,
      "email": "customer@example.com",
      "accepts_marketing": false,
      "created_at": "2024-08-19T10:30:00-04:00",
      "updated_at": "2024-08-19T10:30:00-04:00",
      "first_name": "John",
      "last_name": "Doe",
      "state": "enabled",
      "note": null,
      "verified_email": true,
      "multipass_identifier": null,
      "tax_exempt": false,
      "phone": "+1234567890",
      "email_marketing_consent": {
        "state": "not_subscribed",
        "opt_in_level": "single_opt_in",
        "consent_updated_at": null
      },
      "sms_marketing_consent": {
        "state": "not_subscribed",
        "opt_in_level": "single_opt_in",
        "consent_updated_at": null,
        "consent_collected_from": "SHOPIFY"
      },
      "tags": "whatsapp-customer",
      "currency": "USD",
      "accepts_marketing_updated_at": "2024-08-19T10:30:00-04:00",
      "marketing_opt_in_level": "single_opt_in",
      "tax_exemptions": [],
      "admin_graphql_api_id": "gid://shopify/Customer/6855515070614",
      "default_address": null
    },
    "admin_graphql_api_id": "gid://shopify/DraftOrder/1054381702",
    "invoice_token": "abc123def456"
  }
}
```

### 2. Complete Draft Order

```python
# PUT /admin/api/2024-01/draft_orders/{draft_order_id}/complete.json
async def complete_draft_order(self, draft_order_id: int, payment_pending: bool = False) -> Dict:
    """Complete a draft order to create an actual order"""
    
    complete_payload = {
        "draft_order": {
            "payment_pending": payment_pending
        }
    }
    
    url = f"{self.base_url}/draft_orders/{draft_order_id}/complete.json"
    response = await client.put(url, headers=headers, json=complete_payload)
    
    return response.json()
```

### 3. Send Draft Order Invoice

```python
# POST /admin/api/2024-01/draft_orders/{draft_order_id}/send_invoice.json
async def send_draft_order_invoice(self, draft_order_id: int, email: str) -> Dict:
    """Send invoice email for draft order"""
    
    invoice_payload = {
        "draft_order_invoice": {
            "to": email,
            "from": "noreply@yourstore.com",
            "bcc": ["admin@yourstore.com"],
            "subject": "Complete Your Order - Invoice #{number}",
            "custom_message": "Hi {first_name}, please complete your order by clicking the link below. Thanks for shopping with us!",
        }
    }
    
    url = f"{self.base_url}/draft_orders/{draft_order_id}/send_invoice.json"
    response = await client.post(url, headers=headers, json=invoice_payload)
    
    return response.json()
```

---

## Checkout & Cart APIs

### 1. Cart Permalink Method (Recommended)

```python
async def create_cart_permalink(self, line_items: List[Dict]) -> str:
    """Create a cart permalink URL for instant checkout"""
    
    # Format: /cart/{variant_id}:{quantity},{variant_id}:{quantity}
    cart_params = []
    for item in line_items:
        cart_params.append(f"{item['variant_id']}:{item['quantity']}")
    
    cart_string = ",".join(cart_params)
    checkout_url = f"https://{self.store_url}/cart/{cart_string}"
    
    return checkout_url

# Example URLs:
# Single item: https://store.myshopify.com/cart/45158423330966:2
# Multiple items: https://store.myshopify.com/cart/45158423330966:2,45158423330967:1
```

### 2. Storefront API Cart Creation (GraphQL)

```graphql
# Create cart using Storefront API
mutation cartCreate($input: CartInput!) {
  cartCreate(input: $input) {
    cart {
      id
      checkoutUrl
      estimatedCost {
        totalAmount {
          amount
          currencyCode
        }
        subtotalAmount {
          amount
          currencyCode
        }
        totalTaxAmount {
          amount
          currencyCode
        }
        totalDutyAmount {
          amount
          currencyCode
        }
      }
      lines(first: 100) {
        edges {
          node {
            id
            quantity
            estimatedCost {
              totalAmount {
                amount
                currencyCode
              }
            }
            merchandise {
              ... on ProductVariant {
                id
                title
                price {
                  amount
                  currencyCode
                }
                product {
                  title
                  handle
                }
              }
            }
          }
        }
      }
    }
    userErrors {
      field
      message
    }
  }
}
```

#### Variables for Cart Creation

```json
{
  "input": {
    "lines": [
      {
        "merchandiseId": "gid://shopify/ProductVariant/45158423330966",
        "quantity": 2
      },
      {
        "merchandiseId": "gid://shopify/ProductVariant/45158423330967",
        "quantity": 1
      }
    ],
    "attributes": [
      {
        "key": "source",
        "value": "whatsapp-bot"
      },
      {
        "key": "channel",
        "value": "whatsapp"
      }
    ],
    "note": "Order from WhatsApp Bot",
    "buyerIdentity": {
      "email": "customer@example.com",
      "phone": "+1234567890",
      "countryCode": "US"
    }
  }
}
```

### 3. Update Cart Lines

```graphql
mutation cartLinesUpdate($cartId: ID!, $lines: [CartLineUpdateInput!]!) {
  cartLinesUpdate(cartId: $cartId, lines: $lines) {
    cart {
      id
      checkoutUrl
      estimatedCost {
        totalAmount {
          amount
          currencyCode
        }
      }
      lines(first: 100) {
        edges {
          node {
            id
            quantity
            merchandise {
              ... on ProductVariant {
                id
                title
                price {
                  amount
                  currencyCode
                }
              }
            }
          }
        }
      }
    }
    userErrors {
      field
      message
    }
  }
}
```

---

## API Version Management

### Current API Versions

```python
class ShopifyAPIVersions:
    LATEST = "2024-01"
    SUPPORTED = ["2024-01", "2023-10", "2023-07", "2023-04"]
    DEPRECATED = ["2023-01", "2022-10", "2022-07"]
    
    # Version-specific features
    FEATURES = {
        "2024-01": {
            "draft_orders": True,
            "checkout_api": False,  # Deprecated
            "storefront_api": True,
            "cart_permalinks": True,
            "graphql_admin": True
        },
        "2023-10": {
            "draft_orders": True,
            "checkout_api": True,   # Limited support
            "storefront_api": True,
            "cart_permalinks": True,
            "graphql_admin": True
        }
    }
```

### Version Migration Strategy

```python
async def check_api_version_compatibility(self):
    """Check if current API version supports required features"""
    
    version_info_url = f"https://{self.store_url}/admin/api.json"
    response = await client.get(version_info_url, headers=self.headers)
    
    if response.status_code == 200:
        data = response.json()
        supported_versions = data.get("supported_api_versions", [])
        
        if self.api_version not in supported_versions:
            print(f"Warning: API version {self.api_version} may not be supported")
            
        return supported_versions
    
    return []

# Update base URL based on version
def set_api_version(self, version: str):
    """Set API version for requests"""
    self.api_version = version
    self.base_url = f"https://{self.store_url}/admin/api/{version}"
```

---

## Error Handling

### Common HTTP Status Codes

```python
class ShopifyAPIError(Exception):
    """Custom exception for Shopify API errors"""
    
    def __init__(self, status_code: int, message: str, response_data: dict = None):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data or {}
        super().__init__(f"Shopify API Error {status_code}: {message}")

# Error handling implementation
async def handle_shopify_response(self, response):
    """Handle Shopify API response with proper error checking"""
    
    if response.status_code == 200 or response.status_code == 201:
        return response.json()
    
    error_data = {}
    try:
        error_data = response.json()
    except:
        pass
    
    error_messages = {
        400: "Bad Request - Invalid parameters",
        401: "Unauthorized - Invalid access token", 
        402: "Payment Required - Shop is frozen",
        403: "Forbidden - Access denied",
        404: "Not Found - Resource doesn't exist",
        406: "Not Acceptable - Invalid format",
        422: "Unprocessable Entity - Validation errors",
        423: "Locked - Shop is locked",
        429: "Too Many Requests - Rate limit exceeded",
        500: "Internal Server Error - Shopify issue",
        502: "Bad Gateway - Shopify is down",
        503: "Service Unavailable - Shopify maintenance"
    }
    
    message = error_messages.get(response.status_code, "Unknown error")
    
    # Extract specific error details
    if "errors" in error_data:
        if isinstance(error_data["errors"], dict):
            specific_errors = []
            for field, msgs in error_data["errors"].items():
                if isinstance(msgs, list):
                    specific_errors.extend([f"{field}: {msg}" for msg in msgs])
                else:
                    specific_errors.append(f"{field}: {msgs}")
            message += f" - {'; '.join(specific_errors)}"
        elif isinstance(error_data["errors"], list):
            message += f" - {'; '.join(error_data['errors'])}"
        else:
            message += f" - {error_data['errors']}"
    
    raise ShopifyAPIError(response.status_code, message, error_data)
```

### Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta

class ShopifyRateLimiter:
    """Handle Shopify API rate limiting"""
    
    def __init__(self):
        self.requests_made = 0
        self.window_start = datetime.now()
        self.max_requests = 40  # Default limit
        self.window_size = timedelta(seconds=1)
        
    async def wait_if_needed(self, response_headers: dict):
        """Check rate limit headers and wait if necessary"""
        
        # Check X-Shopify-Shop-Api-Call-Limit header
        call_limit = response_headers.get("X-Shopify-Shop-Api-Call-Limit")
        if call_limit:
            current, max_calls = map(int, call_limit.split("/"))
            
            if current >= max_calls - 5:  # Leave buffer
                wait_time = 1.0  # Wait 1 second
                print(f"Rate limit approaching ({current}/{max_calls}), waiting {wait_time}s")
                await asyncio.sleep(wait_time)
        
        # Check Retry-After header for 429 responses
        retry_after = response_headers.get("Retry-After")
        if retry_after:
            wait_time = int(retry_after)
            print(f"Rate limited, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

# Usage in API calls
async def make_request(self, method: str, url: str, **kwargs):
    """Make API request with rate limiting"""
    
    response = await self.client.request(method, url, **kwargs)
    
    # Handle rate limiting
    await self.rate_limiter.wait_if_needed(response.headers)
    
    # Handle errors
    await self.handle_shopify_response(response)
    
    return response
```

---

## GraphQL vs REST

### When to Use GraphQL

**Advantages:**
- Single endpoint for all operations
- Request exactly the data you need
- Strong type system
- Real-time subscriptions
- Better for complex queries

**Use Cases:**
- Fetching multiple related resources
- Mobile apps with limited bandwidth
- Complex filtering and searching
- Real-time data requirements

### When to Use REST

**Advantages:**
- Simpler to implement and debug
- Better caching support
- Smaller learning curve
- More widespread tooling

**Use Cases:**
- Simple CRUD operations
- File uploads
- Third-party integrations
- Legacy system compatibility

### API Comparison Example

#### REST: Get Product with Variants
```python
# Multiple requests needed
products_response = await client.get(f"{base_url}/products/{product_id}.json")
product = products_response.json()["product"]

variants_response = await client.get(f"{base_url}/products/{product_id}/variants.json")
variants = variants_response.json()["variants"]

images_response = await client.get(f"{base_url}/products/{product_id}/images.json")
images = images_response.json()["images"]
```

#### GraphQL: Get Product with Variants
```graphql
# Single request gets everything
query getProduct($id: ID!) {
  product(id: $id) {
    id
    title
    description
    variants(first: 100) {
      edges {
        node {
          id
          title
          price
          inventoryQuantity
        }
      }
    }
    images(first: 10) {
      edges {
        node {
          id
          url
          altText
        }
      }
    }
  }
}
```

---

## Implementation Examples

### Complete Product Service Implementation

```python
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

class ShopifyProductService:
    """Complete Shopify product management service"""
    
    def __init__(self, store_url: str, access_token: str, api_version: str = "2024-01"):
        self.store_url = store_url
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{store_url}/admin/api/{api_version}"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        self.rate_limiter = ShopifyRateLimiter()
    
    async def get_products(
        self, 
        limit: int = 50,
        page: int = 1,
        status: str = "active",
        vendor: Optional[str] = None,
        product_type: Optional[str] = None,
        collection_id: Optional[int] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None,
        updated_at_min: Optional[datetime] = None,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch products with comprehensive filtering options
        
        Args:
            limit: Number of products to return (max 250)
            page: Page number for pagination
            status: Product status (active, archived, draft)
            vendor: Filter by vendor
            product_type: Filter by product type
            collection_id: Filter by collection
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            updated_at_min: Minimum update date
            fields: Specific fields to return
            
        Returns:
            List of product dictionaries
        """
        
        params = {
            "limit": min(limit, 250),
            "page": page,
            "status": status
        }
        
        # Add optional filters
        if vendor:
            params["vendor"] = vendor
        if product_type:
            params["product_type"] = product_type
        if collection_id:
            params["collection_id"] = collection_id
        if created_at_min:
            params["created_at_min"] = created_at_min.isoformat()
        if created_at_max:
            params["created_at_max"] = created_at_max.isoformat()
        if updated_at_min:
            params["updated_at_min"] = updated_at_min.isoformat()
        if fields:
            params["fields"] = ",".join(fields)
        
        url = f"{self.base_url}/products.json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            await self.rate_limiter.wait_if_needed(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_products(data.get("products", []))
            else:
                await self.handle_shopify_response(response)
                return []
    
    async def get_product(self, product_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a specific product by ID
        
        Args:
            product_id: Shopify product ID
            fields: Specific fields to return
            
        Returns:
            Product dictionary or empty dict if not found
        """
        
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        url = f"{self.base_url}/products/{product_id}.json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            await self.rate_limiter.wait_if_needed(response.headers)
            
            if response.status_code == 200:
                product = response.json()["product"]
                return self._process_product(product)
            elif response.status_code == 404:
                return {}
            else:
                await self.handle_shopify_response(response)
                return {}
    
    async def search_products(
        self, 
        query: str, 
        limit: int = 20,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search products using Shopify's search functionality
        
        Args:
            query: Search query (supports title, vendor, product_type, tag filters)
            limit: Number of results to return
            fields: Specific fields to return
            
        Returns:
            List of matching products
            
        Example queries:
            "title:*shirt*" - Products with "shirt" in title
            "vendor:Nike" - Products from Nike
            "product_type:Clothing" - Clothing products
            "tag:sale" - Products tagged with "sale"
            "title:*premium* AND vendor:Nike" - Complex query
        """
        
        params = {
            "limit": min(limit, 250),
            "fields": ",".join(fields) if fields else "id,title,handle,vendor,product_type,variants"
        }
        
        # Use the search endpoint
        url = f"{self.base_url}/products.json"
        
        # Add search query to URL
        search_url = f"{url}?{query}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=self.headers, params=params)
            await self.rate_limiter.wait_if_needed(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_products(data.get("products", []))
            else:
                await self.handle_shopify_response(response)
                return []
    
    async def get_product_variants(self, product_id: str) -> List[Dict[str, Any]]:
        """Get all variants for a specific product"""
        
        url = f"{self.base_url}/products/{product_id}/variants.json"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            await self.rate_limiter.wait_if_needed(response.headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("variants", [])
            else:
                await self.handle_shopify_response(response)
                return []
    
    async def check_inventory(self, variant_ids: List[str]) -> Dict[str, int]:
        """
        Check inventory levels for multiple variants
        
        Args:
            variant_ids: List of variant IDs to check
            
        Returns:
            Dictionary mapping variant_id to inventory_quantity
        """
        
        inventory_levels = {}
        
        # Get inventory items for variants
        for variant_id in variant_ids:
            url = f"{self.base_url}/variants/{variant_id}.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                await self.rate_limiter.wait_if_needed(response.headers)
                
                if response.status_code == 200:
                    variant = response.json()["variant"]
                    inventory_levels[variant_id] = variant.get("inventory_quantity", 0)
                else:
                    inventory_levels[variant_id] = 0
        
        return inventory_levels
    
    def _process_products(self, products: List[Dict]) -> List[Dict[str, Any]]:
        """Process raw product data for consistent format"""
        
        processed_products = []
        
        for product in products:
            processed_product = self._process_product(product)
            processed_products.append(processed_product)
        
        return processed_products
    
    def _process_product(self, product: Dict) -> Dict[str, Any]:
        """Process a single product for consistent format"""
        
        # Get the first variant for basic product info
        variant = product.get("variants", [{}])[0]
        
        # Clean up description by removing HTML tags
        description = product.get("body_html", "")
        if description:
            import re
            description = re.sub(r'<[^>]+>', '', str(description))
            description = description.replace("&nbsp;", " ").strip()
        
        # Get the primary image
        image = None
        if product.get("images"):
            image = product["images"][0]["src"]
        elif product.get("image"):
            image = product["image"]["src"]
        
        return {
            "id": str(product["id"]),
            "title": product.get("title", ""),
            "description": description,
            "handle": product.get("handle", ""),
            "vendor": product.get("vendor", ""),
            "product_type": product.get("product_type", ""),
            "tags": product.get("tags", "").split(", ") if product.get("tags") else [],
            "status": product.get("status", ""),
            "created_at": product.get("created_at"),
            "updated_at": product.get("updated_at"),
            "published_at": product.get("published_at"),
            "price": variant.get("price", "0.00"),
            "compare_at_price": variant.get("compare_at_price"),
            "sku": variant.get("sku", ""),
            "barcode": variant.get("barcode"),
            "inventory_quantity": variant.get("inventory_quantity", 0),
            "weight": variant.get("weight", 0),
            "weight_unit": variant.get("weight_unit", "kg"),
            "requires_shipping": variant.get("requires_shipping", True),
            "taxable": variant.get("taxable", True),
            "variant_id": str(variant.get("id", "")),
            "variant_title": variant.get("title", ""),
            "image": image,
            "images": [img["src"] for img in product.get("images", [])],
            "variants": product.get("variants", []),
            "options": product.get("options", []),
            "admin_graphql_api_id": product.get("admin_graphql_api_id"),
            "url": f"https://{self.store_url}/products/{product.get('handle', '')}"
        }
```

---

## Testing & Debugging

### API Testing Tools

#### 1. Postman Collection Setup

```json
{
  "info": {
    "name": "Shopify API Testing",
    "description": "Collection for testing Shopify REST and GraphQL APIs"
  },
  "variable": [
    {
      "key": "store_url",
      "value": "your-store.myshopify.com"
    },
    {
      "key": "access_token", 
      "value": "shpat_your_access_token_here"
    },
    {
      "key": "api_version",
      "value": "2024-01"
    },
    {
      "key": "base_url",
      "value": "https://{{store_url}}/admin/api/{{api_version}}"
    }
  ],
  "auth": {
    "type": "apikey",
    "apikey": [
      {
        "key": "key",
        "value": "X-Shopify-Access-Token"
      },
      {
        "key": "value",
        "value": "{{access_token}}"
      }
    ]
  }
}
```

#### 2. cURL Testing Examples

```bash
# Test API connection
curl -X GET "https://your-store.myshopify.com/admin/api/2024-01/shop.json" \
  -H "X-Shopify-Access-Token: your_access_token"

# Get products
curl -X GET "https://your-store.myshopify.com/admin/api/2024-01/products.json?limit=5" \
  -H "X-Shopify-Access-Token: your_access_token"

# Create draft order
curl -X POST "https://your-store.myshopify.com/admin/api/2024-01/draft_orders.json" \
  -H "X-Shopify-Access-Token: your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "draft_order": {
      "line_items": [
        {
          "variant_id": 45158423330966,
          "quantity": 1
        }
      ]
    }
  }'

# GraphQL query
curl -X POST "https://your-store.myshopify.com/admin/api/2024-01/graphql.json" \
  -H "X-Shopify-Access-Token: your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ shop { name email } }"
  }'
```

### Debug Logging Implementation

```python
import logging
import json
from datetime import datetime

class ShopifyAPILogger:
    """Comprehensive logging for Shopify API interactions"""
    
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger("shopify_api")
        self.logger.setLevel(log_level)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler('shopify_api.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_request(self, method: str, url: str, headers: dict, data: dict = None):
        """Log API request details"""
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "method": method,
            "url": url,
            "headers": {k: v for k, v in headers.items() if k != "X-Shopify-Access-Token"},
            "data": data
        }
        
        self.logger.info(f"API Request: {json.dumps(log_data, indent=2)}")
    
    def log_response(self, response, duration: float):
        """Log API response details"""
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "response", 
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "duration_ms": round(duration * 1000, 2),
            "response_size": len(response.content) if response.content else 0
        }
        
        # Add response data for successful requests
        if response.status_code < 400:
            try:
                log_data["data"] = response.json()
            except:
                log_data["data"] = response.text[:500] + "..." if len(response.text) > 500 else response.text
        
        level = logging.INFO if response.status_code < 400 else logging.ERROR
        self.logger.log(level, f"API Response: {json.dumps(log_data, indent=2)}")
    
    def log_error(self, error: Exception, context: dict = None):
        """Log API errors with context"""
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        self.logger.error(f"API Error: {json.dumps(log_data, indent=2)}")

# Usage in API service
class ShopifyService:
    def __init__(self, store_url: str, access_token: str):
        self.store_url = store_url
        self.access_token = access_token
        self.logger = ShopifyAPILogger()
    
    async def make_request(self, method: str, url: str, **kwargs):
        """Make API request with comprehensive logging"""
        
        start_time = time.time()
        
        # Log request
        self.logger.log_request(method, url, kwargs.get('headers', {}), kwargs.get('json'))
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, **kwargs)
                
                # Log response
                duration = time.time() - start_time
                self.logger.log_response(response, duration)
                
                return response
                
        except Exception as e:
            # Log error
            context = {
                "method": method,
                "url": url,
                "duration": time.time() - start_time
            }
            self.logger.log_error(e, context)
            raise
```

### Testing Scenarios

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

class TestShopifyProductService:
    """Test suite for Shopify product service"""
    
    @pytest.fixture
    def shopify_service(self):
        return ShopifyProductService(
            store_url="test-store.myshopify.com",
            access_token="test_token"
        )
    
    @pytest.mark.asyncio
    async def test_get_products_success(self, shopify_service):
        """Test successful product retrieval"""
        
        mock_response = {
            "products": [
                {
                    "id": 8394948493462,
                    "title": "Test Product",
                    "body_html": "<p>Test description</p>",
                    "variants": [{
                        "id": 45158423330966,
                        "price": "25.00",
                        "inventory_quantity": 10
                    }],
                    "images": [{"src": "https://example.com/image.jpg"}]
                }
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.headers = {}
            mock_get.return_value = mock_response_obj
            
            products = await shopify_service.get_products(limit=1)
            
            assert len(products) == 1
            assert products[0]["title"] == "Test Product"
            assert products[0]["price"] == "25.00"
            assert products[0]["description"] == "Test description"
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, shopify_service):
        """Test product not found scenario"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status_code = 404
            mock_get.return_value = mock_response_obj
            
            product = await shopify_service.get_product("999999")
            
            assert product == {}
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, shopify_service):
        """Test rate limiting behavior"""
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status_code = 429
            mock_response_obj.headers = {"Retry-After": "1"}
            mock_get.return_value = mock_response_obj
            
            with patch('asyncio.sleep') as mock_sleep:
                try:
                    await shopify_service.get_products()
                except ShopifyAPIError:
                    pass
                
                # Verify sleep was called with retry delay
                mock_sleep.assert_called_with(1)

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Conclusion

This comprehensive documentation covers all aspects of Shopify API integration for the WhatsApp bot, including:

- **Complete API references** for products, orders, and checkouts
- **Both REST and GraphQL** implementations
- **Real-world examples** with full response structures
- **Error handling** and rate limiting strategies
- **Testing and debugging** tools and techniques
- **Production-ready code** examples

Use this documentation as your complete reference for understanding and implementing Shopify API functionality in your WhatsApp bot or any other application.

## Additional Resources

- [Shopify Admin API Documentation](https://shopify.dev/docs/api/admin-rest)
- [Shopify GraphQL Admin API](https://shopify.dev/docs/api/admin-graphql)
- [Shopify Storefront API](https://shopify.dev/docs/api/storefront)
- [Shopify Webhooks](https://shopify.dev/docs/api/webhooks)
- [Shopify Rate Limits](https://shopify.dev/docs/api/usage/rate-limits)