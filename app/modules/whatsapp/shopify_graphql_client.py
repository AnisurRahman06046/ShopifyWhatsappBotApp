import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ShopifyGraphQLClient:
    """
    Complete GraphQL client for Shopify Admin API
    Provides methods to query products, orders, customers, draft orders, shop info, and webhooks using GraphQL
    """

    def __init__(self, store_url: str, access_token: str, api_version: str = "2025-01"):
        self.store_url = store_url
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{store_url}/admin/api/{api_version}/graphql.json"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }

    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against Shopify Admin API"""
        
        payload = {
            "query": query
        }
        
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check for GraphQL errors
                    if "errors" in result:
                        print(f"[ERROR] GraphQL errors: {result['errors']}")
                        return {"error": "GraphQL query failed", "details": result["errors"]}
                    
                    return result.get("data", {})
                
                elif response.status_code == 429:
                    # Rate limited
                    print("[WARNING] GraphQL request rate limited")
                    return {"error": "rate_limited"}
                
                else:
                    print(f"[ERROR] GraphQL request failed: {response.status_code}")
                    print(f"[ERROR] Response: {response.text}")
                    return {"error": f"HTTP {response.status_code}", "details": response.text}
                    
            except Exception as e:
                print(f"[ERROR] GraphQL request exception: {str(e)}")
                return {"error": "request_exception", "details": str(e)}

    async def get_products(self, first: int = 50, after: Optional[str] = None, query: str = "status:active") -> Dict[str, Any]:
        """
        Fetch products using GraphQL
        Returns products with variants and images in a single request
        """
        
        graphql_query = """
        query getProducts($first: Int!, $after: String, $query: String) {
          products(first: $first, after: $after, query: $query) {
            edges {
              node {
                id
                legacyResourceId
                title
                description
                productType
                vendor
                status
                handle
                tags
                createdAt
                updatedAt
                publishedAt
                variants(first: 100) {
                  edges {
                    node {
                      id
                      legacyResourceId
                      title
                      price
                      compareAtPrice
                      sku
                      inventoryQuantity
                      inventoryPolicy
                      taxable
                      position
                      availableForSale
                      createdAt
                      updatedAt
                    }
                  }
                }
                images(first: 10) {
                  edges {
                    node {
                      id
                      altText
                      url
                      width
                      height
                    }
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
        """
        
        variables = {
            "first": first,
            "query": query
        }
        
        if after:
            variables["after"] = after
        
        return await self.execute_query(graphql_query, variables)

    async def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """
        Fetch a single product by ID using GraphQL
        Supports both legacy ID (numeric) and GraphQL ID (gid://shopify/Product/...)
        """
        
        # Convert legacy ID to GraphQL ID if needed
        if product_id.isdigit():
            gql_id = f"gid://shopify/Product/{product_id}"
        else:
            gql_id = product_id
        
        graphql_query = """
        query getProduct($id: ID!) {
          product(id: $id) {
            id
            legacyResourceId
            title
            description
            productType
            vendor
            status
            handle
            tags
            createdAt
            updatedAt
            publishedAt
            variants(first: 100) {
              edges {
                node {
                  id
                  legacyResourceId
                  title
                  price
                  compareAtPrice
                  sku
                  inventoryQuantity
                  inventoryPolicy
                  taxable
                  position
                  availableForSale
                  createdAt
                  updatedAt
                }
              }
            }
            images(first: 10) {
              edges {
                node {
                  id
                  altText
                  url
                  width
                  height
                }
              }
            }
          }
        }
        """
        
        variables = {"id": gql_id}
        result = await self.execute_query(graphql_query, variables)
        
        return result

    async def get_products_count(self, query: str = "status:active") -> Dict[str, Any]:
        """Get total count of products using GraphQL"""
        
        graphql_query = """
        query getProductsCount($query: String) {
          products(first: 0, query: $query) {
            totalCount
          }
        }
        """
        
        variables = {"query": query}
        return await self.execute_query(graphql_query, variables)

    async def get_all_products(self, limit_per_page: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch all products using cursor-based pagination
        Similar to the REST API _fetch_all_products method but using GraphQL
        """
        
        all_products = []
        has_next_page = True
        after_cursor = None
        
        while has_next_page:
            try:
                result = await self.get_products(first=limit_per_page, after=after_cursor)
                
                if "error" in result:
                    if result["error"] == "rate_limited":
                        print("[WARNING] Rate limited, waiting 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        print(f"[ERROR] Failed to fetch products: {result}")
                        break
                
                products_data = result.get("products", {})
                edges = products_data.get("edges", [])
                
                if not edges:
                    break
                
                # Extract products from GraphQL response
                for edge in edges:
                    product = edge.get("node", {})
                    all_products.append(product)
                
                # Check pagination
                page_info = products_data.get("pageInfo", {})
                has_next_page = page_info.get("hasNextPage", False)
                after_cursor = page_info.get("endCursor")
                
                print(f"[INFO] Fetched {len(edges)} products via GraphQL (total: {len(all_products)})")
                
                # Small delay to be nice to the API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] Exception while fetching products via GraphQL: {str(e)}")
                break
        
        return all_products

    def convert_graphql_to_rest_format(self, graphql_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert GraphQL product response to REST API format
        This ensures backward compatibility with existing code
        """
        
        # Extract basic product info
        rest_product = {
            "id": int(graphql_product.get("legacyResourceId", 0)),
            "title": graphql_product.get("title", ""),
            "body_html": graphql_product.get("description", ""),
            "vendor": graphql_product.get("vendor", ""),
            "product_type": graphql_product.get("productType", ""),
            "created_at": graphql_product.get("createdAt", ""),
            "updated_at": graphql_product.get("updatedAt", ""),
            "published_at": graphql_product.get("publishedAt", ""),
            "status": graphql_product.get("status", "").lower(),
            "handle": graphql_product.get("handle", ""),
            "tags": graphql_product.get("tags", []),
            "admin_graphql_api_id": graphql_product.get("id", "")
        }
        
        # Convert tags list to comma-separated string if needed
        if isinstance(rest_product["tags"], list):
            rest_product["tags"] = ", ".join(rest_product["tags"])
        
        # Convert variants
        variants = []
        variant_edges = graphql_product.get("variants", {}).get("edges", [])
        for variant_edge in variant_edges:
            variant_node = variant_edge.get("node", {})
            rest_variant = {
                "id": int(variant_node.get("legacyResourceId", 0)),
                "product_id": rest_product["id"],
                "title": variant_node.get("title", ""),
                "price": variant_node.get("price", "0.00"),
                "compare_at_price": variant_node.get("compareAtPrice"),
                "sku": variant_node.get("sku", ""),
                "position": variant_node.get("position", 1),
                "inventory_policy": variant_node.get("inventoryPolicy", "").lower(),
                "inventory_management": None,  # Not available in GraphQL
                "inventory_quantity": variant_node.get("inventoryQuantity", 0),
                "taxable": variant_node.get("taxable", True),
                "requires_shipping": True,  # Default value
                "weight": 0,  # Not available in GraphQL
                "weight_unit": "kg",  # Default value
                "created_at": variant_node.get("createdAt", ""),
                "updated_at": variant_node.get("updatedAt", ""),
                "admin_graphql_api_id": variant_node.get("id", ""),
                "available": variant_node.get("availableForSale", True)
            }
            variants.append(rest_variant)
        
        rest_product["variants"] = variants
        
        # Convert images
        images = []
        image_edges = graphql_product.get("images", {}).get("edges", [])
        for i, image_edge in enumerate(image_edges, 1):
            image_node = image_edge.get("node", {})
            rest_image = {
                "id": 0,  # legacyResourceId not available for images in GraphQL
                "product_id": rest_product["id"],
                "position": i,
                "created_at": graphql_product.get("createdAt", ""),
                "updated_at": graphql_product.get("updatedAt", ""),
                "alt": image_node.get("altText"),
                "width": image_node.get("width"),
                "height": image_node.get("height"),
                "src": image_node.get("url", ""),
                "admin_graphql_api_id": image_node.get("id", "")
            }
            images.append(rest_image)
        
        rest_product["images"] = images
        
        return rest_product

    # ============================================================================
    # ORDERS GraphQL Methods
    # ============================================================================

    async def get_orders(self, first: int = 50, after: Optional[str] = None, query: str = "") -> Dict[str, Any]:
        """
        Fetch orders using GraphQL
        """
        
        graphql_query = """
        query getOrders($first: Int!, $after: String, $query: String) {
          orders(first: $first, after: $after, query: $query) {
            edges {
              node {
                id
                legacyResourceId
                name
                email
                createdAt
                updatedAt
                processedAt
                cancelledAt
                cancelReason
                financialStatus
                fulfillmentStatus
                totalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                subtotalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                totalTaxSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                totalShippingPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                customer {
                  id
                  legacyResourceId
                  firstName
                  lastName
                  email
                  phone
                }
                shippingAddress {
                  firstName
                  lastName
                  company
                  address1
                  address2
                  city
                  province
                  country
                  zip
                  phone
                }
                billingAddress {
                  firstName
                  lastName
                  company
                  address1
                  address2
                  city
                  province
                  country
                  zip
                  phone
                }
                lineItems(first: 100) {
                  edges {
                    node {
                      id
                      title
                      quantity
                      originalUnitPriceSet {
                        shopMoney {
                          amount
                          currencyCode
                        }
                      }
                      variant {
                        id
                        legacyResourceId
                        sku
                        title
                      }
                      product {
                        id
                        legacyResourceId
                        title
                        handle
                      }
                    }
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
        """
        
        variables = {
            "first": first,
            "query": query
        }
        
        if after:
            variables["after"] = after
        
        return await self.execute_query(graphql_query, variables)

    async def get_order_by_id(self, order_id: str) -> Dict[str, Any]:
        """Fetch a single order by ID"""
        
        # Convert legacy ID to GraphQL ID if needed
        if order_id.isdigit():
            gql_id = f"gid://shopify/Order/{order_id}"
        else:
            gql_id = order_id
        
        graphql_query = """
        query getOrder($id: ID!) {
          order(id: $id) {
            id
            legacyResourceId
            name
            email
            createdAt
            updatedAt
            processedAt
            cancelledAt
            cancelReason
            financialStatus
            fulfillmentStatus
            totalPriceSet {
              shopMoney {
                amount
                currencyCode
              }
            }
            subtotalPriceSet {
              shopMoney {
                amount
                currencyCode
              }
            }
            customer {
              id
              legacyResourceId
              firstName
              lastName
              email
              phone
            }
            lineItems(first: 100) {
              edges {
                node {
                  id
                  title
                  quantity
                  originalUnitPriceSet {
                    shopMoney {
                      amount
                      currencyCode
                    }
                  }
                  variant {
                    id
                    legacyResourceId
                    sku
                    title
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {"id": gql_id}
        return await self.execute_query(graphql_query, variables)

    async def get_orders_count(self, query: str = "") -> Dict[str, Any]:
        """Get total count of orders using GraphQL"""
        
        graphql_query = """
        query getOrdersCount($query: String) {
          orders(first: 0, query: $query) {
            totalCount
          }
        }
        """
        
        variables = {"query": query}
        return await self.execute_query(graphql_query, variables)

    # ============================================================================
    # CUSTOMERS GraphQL Methods
    # ============================================================================

    async def get_customers(self, first: int = 50, after: Optional[str] = None, query: str = "") -> Dict[str, Any]:
        """Fetch customers using GraphQL"""
        
        graphql_query = """
        query getCustomers($first: Int!, $after: String, $query: String) {
          customers(first: $first, after: $after, query: $query) {
            edges {
              node {
                id
                legacyResourceId
                firstName
                lastName
                displayName
                email
                phone
                createdAt
                updatedAt
                acceptsMarketing
                ordersCount
                totalSpentV2 {
                  amount
                  currencyCode
                }
                defaultAddress {
                  id
                  firstName
                  lastName
                  company
                  address1
                  address2
                  city
                  province
                  country
                  zip
                  phone
                }
                addresses(first: 10) {
                  edges {
                    node {
                      id
                      firstName
                      lastName
                      company
                      address1
                      address2
                      city
                      province
                      country
                      zip
                      phone
                    }
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
        """
        
        variables = {
            "first": first,
            "query": query
        }
        
        if after:
            variables["after"] = after
        
        return await self.execute_query(graphql_query, variables)

    async def get_customer_by_id(self, customer_id: str) -> Dict[str, Any]:
        """Fetch a single customer by ID"""
        
        # Convert legacy ID to GraphQL ID if needed
        if customer_id.isdigit():
            gql_id = f"gid://shopify/Customer/{customer_id}"
        else:
            gql_id = customer_id
        
        graphql_query = """
        query getCustomer($id: ID!) {
          customer(id: $id) {
            id
            legacyResourceId
            firstName
            lastName
            displayName
            email
            phone
            createdAt
            updatedAt
            acceptsMarketing
            ordersCount
            totalSpentV2 {
              amount
              currencyCode
            }
            defaultAddress {
              id
              firstName
              lastName
              company
              address1
              address2
              city
              province
              country
              zip
              phone
            }
            addresses(first: 10) {
              edges {
                node {
                  id
                  firstName
                  lastName
                  company
                  address1
                  address2
                  city
                  province
                  country
                  zip
                  phone
                }
              }
            }
          }
        }
        """
        
        variables = {"id": gql_id}
        return await self.execute_query(graphql_query, variables)

    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer using GraphQL mutation"""
        
        graphql_mutation = """
        mutation customerCreate($input: CustomerInput!) {
          customerCreate(input: $input) {
            customer {
              id
              legacyResourceId
              firstName
              lastName
              email
              phone
              createdAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": customer_data
        }
        
        return await self.execute_query(graphql_mutation, variables)

    # ============================================================================
    # DRAFT ORDERS GraphQL Methods
    # ============================================================================

    async def get_draft_orders(self, first: int = 50, after: Optional[str] = None) -> Dict[str, Any]:
        """Fetch draft orders using GraphQL"""
        
        graphql_query = """
        query getDraftOrders($first: Int!, $after: String) {
          draftOrders(first: $first, after: $after) {
            edges {
              node {
                id
                legacyResourceId
                name
                email
                createdAt
                updatedAt
                invoiceUrl
                status
                totalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                subtotalPriceSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                totalTaxSet {
                  shopMoney {
                    amount
                    currencyCode
                  }
                }
                customer {
                  id
                  legacyResourceId
                  firstName
                  lastName
                  email
                  phone
                }
                shippingAddress {
                  firstName
                  lastName
                  company
                  address1
                  address2
                  city
                  province
                  country
                  zip
                  phone
                }
                billingAddress {
                  firstName
                  lastName
                  company
                  address1
                  address2
                  city
                  province
                  country
                  zip
                  phone
                }
                lineItems(first: 100) {
                  edges {
                    node {
                      id
                      title
                      quantity
                      originalUnitPriceSet {
                        shopMoney {
                          amount
                          currencyCode
                        }
                      }
                      variant {
                        id
                        legacyResourceId
                        sku
                        title
                      }
                      product {
                        id
                        legacyResourceId
                        title
                        handle
                      }
                    }
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
        """
        
        variables = {
            "first": first
        }
        
        if after:
            variables["after"] = after
        
        return await self.execute_query(graphql_query, variables)

    async def create_draft_order(self, draft_order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a draft order using GraphQL mutation"""
        
        graphql_mutation = """
        mutation draftOrderCreate($input: DraftOrderInput!) {
          draftOrderCreate(input: $input) {
            draftOrder {
              id
              legacyResourceId
              name
              email
              invoiceUrl
              status
              totalPriceSet {
                shopMoney {
                  amount
                  currencyCode
                }
              }
              createdAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "input": draft_order_data
        }
        
        return await self.execute_query(graphql_mutation, variables)

    async def complete_draft_order(self, draft_order_id: str) -> Dict[str, Any]:
        """Complete a draft order using GraphQL mutation"""
        
        # Convert legacy ID to GraphQL ID if needed
        if draft_order_id.isdigit():
            gql_id = f"gid://shopify/DraftOrder/{draft_order_id}"
        else:
            gql_id = draft_order_id
        
        graphql_mutation = """
        mutation draftOrderComplete($id: ID!) {
          draftOrderComplete(id: $id) {
            draftOrder {
              id
              legacyResourceId
              status
            }
            order {
              id
              legacyResourceId
              name
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {"id": gql_id}
        return await self.execute_query(graphql_mutation, variables)

    # ============================================================================
    # SHOP GraphQL Methods
    # ============================================================================

    async def get_shop_info(self) -> Dict[str, Any]:
        """Get shop information using GraphQL"""
        
        graphql_query = """
        query getShop {
          shop {
            id
            name
            description
            email
            domain
            myshopifyDomain
            url
            currencyCode
            timezoneOffsetMinutes
            plan {
              displayName
              partnerDevelopment
              shopifyPlus
            }
            primaryDomain {
              host
              sslEnabled
              url
            }
            billingAddress {
              firstName
              lastName
              company
              address1
              address2
              city
              province
              country
              zip
              phone
            }
            createdAt
            updatedAt
            enabled
            setupRequired
            taxesIncluded
            taxShipping
            countyTaxes
            checkoutApiSupported
            multiLocationEnabled
            hasStorefront
            hasDiscounts
            hasGiftCards
          }
        }
        """
        
        return await self.execute_query(graphql_query)

    # ============================================================================
    # WEBHOOKS GraphQL Methods
    # ============================================================================

    async def get_webhooks(self) -> Dict[str, Any]:
        """Get webhooks using GraphQL"""
        
        graphql_query = """
        query getWebhooks {
          webhookSubscriptions(first: 100) {
            edges {
              node {
                id
                legacyResourceId
                callbackUrl
                topic
                format
                createdAt
                updatedAt
              }
            }
          }
        }
        """
        
        return await self.execute_query(graphql_query)

    async def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a webhook using GraphQL mutation"""
        
        graphql_mutation = """
        mutation webhookSubscriptionCreate($topic: WebhookSubscriptionTopic!, $webhookSubscription: WebhookSubscriptionInput!) {
          webhookSubscriptionCreate(topic: $topic, webhookSubscription: $webhookSubscription) {
            webhookSubscription {
              id
              legacyResourceId
              callbackUrl
              topic
              format
              createdAt
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "topic": webhook_data.get("topic"),
            "webhookSubscription": {
                "callbackUrl": webhook_data.get("address"),
                "format": webhook_data.get("format", "JSON")
            }
        }
        
        return await self.execute_query(graphql_mutation, variables)

    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook using GraphQL mutation"""
        
        # Convert legacy ID to GraphQL ID if needed
        if webhook_id.isdigit():
            gql_id = f"gid://shopify/WebhookSubscription/{webhook_id}"
        else:
            gql_id = webhook_id
        
        graphql_mutation = """
        mutation webhookSubscriptionDelete($id: ID!) {
          webhookSubscriptionDelete(id: $id) {
            deletedWebhookSubscriptionId
            userErrors {
              field
              message
            }
          }
        }
        """
        
        variables = {"id": gql_id}
        return await self.execute_query(graphql_mutation, variables)

    # ============================================================================
    # CONVERSION METHODS (GraphQL to REST format)
    # ============================================================================

    def convert_order_graphql_to_rest(self, graphql_order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GraphQL order response to REST format"""
        
        rest_order = {
            "id": int(graphql_order.get("legacyResourceId", 0)),
            "name": graphql_order.get("name", ""),
            "email": graphql_order.get("email", ""),
            "created_at": graphql_order.get("createdAt", ""),
            "updated_at": graphql_order.get("updatedAt", ""),
            "processed_at": graphql_order.get("processedAt", ""),
            "cancelled_at": graphql_order.get("cancelledAt"),
            "cancel_reason": graphql_order.get("cancelReason"),
            "financial_status": graphql_order.get("financialStatus", "").lower(),
            "fulfillment_status": graphql_order.get("fulfillmentStatus", "").lower(),
            "total_price": graphql_order.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", "0.00"),
            "subtotal_price": graphql_order.get("subtotalPriceSet", {}).get("shopMoney", {}).get("amount", "0.00"),
            "total_tax": graphql_order.get("totalTaxSet", {}).get("shopMoney", {}).get("amount", "0.00"),
            "currency": graphql_order.get("totalPriceSet", {}).get("shopMoney", {}).get("currencyCode", "USD"),
            "admin_graphql_api_id": graphql_order.get("id", "")
        }
        
        # Convert customer
        customer_data = graphql_order.get("customer", {})
        if customer_data:
            rest_order["customer"] = {
                "id": int(customer_data.get("legacyResourceId", 0)),
                "first_name": customer_data.get("firstName", ""),
                "last_name": customer_data.get("lastName", ""),
                "email": customer_data.get("email", ""),
                "phone": customer_data.get("phone", ""),
                "admin_graphql_api_id": customer_data.get("id", "")
            }
        
        # Convert line items
        line_items = []
        line_item_edges = graphql_order.get("lineItems", {}).get("edges", [])
        for item_edge in line_item_edges:
            item_node = item_edge.get("node", {})
            variant_data = item_node.get("variant", {})
            product_data = item_node.get("product", {})
            
            rest_line_item = {
                "id": int(item_node.get("id", "").split("/")[-1]) if item_node.get("id") else 0,
                "title": item_node.get("title", ""),
                "quantity": item_node.get("quantity", 0),
                "price": item_node.get("originalUnitPriceSet", {}).get("shopMoney", {}).get("amount", "0.00"),
                "variant_id": int(variant_data.get("legacyResourceId", 0)) if variant_data.get("legacyResourceId") else None,
                "product_id": int(product_data.get("legacyResourceId", 0)) if product_data.get("legacyResourceId") else None,
                "sku": variant_data.get("sku", ""),
                "variant_title": variant_data.get("title", ""),
                "product_title": product_data.get("title", ""),
                "admin_graphql_api_id": item_node.get("id", "")
            }
            line_items.append(rest_line_item)
        
        rest_order["line_items"] = line_items
        
        # Convert addresses
        shipping_address = graphql_order.get("shippingAddress", {})
        if shipping_address:
            rest_order["shipping_address"] = {
                "first_name": shipping_address.get("firstName", ""),
                "last_name": shipping_address.get("lastName", ""),
                "company": shipping_address.get("company", ""),
                "address1": shipping_address.get("address1", ""),
                "address2": shipping_address.get("address2", ""),
                "city": shipping_address.get("city", ""),
                "province": shipping_address.get("province", ""),
                "country": shipping_address.get("country", ""),
                "zip": shipping_address.get("zip", ""),
                "phone": shipping_address.get("phone", "")
            }
        
        billing_address = graphql_order.get("billingAddress", {})
        if billing_address:
            rest_order["billing_address"] = {
                "first_name": billing_address.get("firstName", ""),
                "last_name": billing_address.get("lastName", ""),
                "company": billing_address.get("company", ""),
                "address1": billing_address.get("address1", ""),
                "address2": billing_address.get("address2", ""),
                "city": billing_address.get("city", ""),
                "province": billing_address.get("province", ""),
                "country": billing_address.get("country", ""),
                "zip": billing_address.get("zip", ""),
                "phone": billing_address.get("phone", "")
            }
        
        return rest_order

    def convert_customer_graphql_to_rest(self, graphql_customer: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GraphQL customer response to REST format"""
        
        rest_customer = {
            "id": int(graphql_customer.get("legacyResourceId", 0)),
            "first_name": graphql_customer.get("firstName", ""),
            "last_name": graphql_customer.get("lastName", ""),
            "email": graphql_customer.get("email", ""),
            "phone": graphql_customer.get("phone", ""),
            "created_at": graphql_customer.get("createdAt", ""),
            "updated_at": graphql_customer.get("updatedAt", ""),
            "accepts_marketing": graphql_customer.get("acceptsMarketing", False),
            "orders_count": graphql_customer.get("ordersCount", 0),
            "total_spent": graphql_customer.get("totalSpentV2", {}).get("amount", "0.00"),
            "currency": graphql_customer.get("totalSpentV2", {}).get("currencyCode", "USD"),
            "admin_graphql_api_id": graphql_customer.get("id", "")
        }
        
        # Convert default address
        default_address = graphql_customer.get("defaultAddress", {})
        if default_address:
            rest_customer["default_address"] = {
                "id": int(default_address.get("id", "").split("/")[-1]) if default_address.get("id") else 0,
                "first_name": default_address.get("firstName", ""),
                "last_name": default_address.get("lastName", ""),
                "company": default_address.get("company", ""),
                "address1": default_address.get("address1", ""),
                "address2": default_address.get("address2", ""),
                "city": default_address.get("city", ""),
                "province": default_address.get("province", ""),
                "country": default_address.get("country", ""),
                "zip": default_address.get("zip", ""),
                "phone": default_address.get("phone", "")
            }
        
        # Convert addresses
        addresses = []
        address_edges = graphql_customer.get("addresses", {}).get("edges", [])
        for address_edge in address_edges:
            address_node = address_edge.get("node", {})
            rest_address = {
                "id": int(address_node.get("id", "").split("/")[-1]) if address_node.get("id") else 0,
                "first_name": address_node.get("firstName", ""),
                "last_name": address_node.get("lastName", ""),
                "company": address_node.get("company", ""),
                "address1": address_node.get("address1", ""),
                "address2": address_node.get("address2", ""),
                "city": address_node.get("city", ""),
                "province": address_node.get("province", ""),
                "country": address_node.get("country", ""),
                "zip": address_node.get("zip", ""),
                "phone": address_node.get("phone", "")
            }
            addresses.append(rest_address)
        
        rest_customer["addresses"] = addresses
        
        return rest_customer

    def convert_shop_graphql_to_rest(self, graphql_shop: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GraphQL shop response to REST format"""
        
        rest_shop = {
            "id": int(graphql_shop.get("id", "").split("/")[-1]) if graphql_shop.get("id") else 0,
            "name": graphql_shop.get("name", ""),
            "email": graphql_shop.get("email", ""),
            "domain": graphql_shop.get("domain", ""),
            "myshopify_domain": graphql_shop.get("myshopifyDomain", ""),
            "currency": graphql_shop.get("currencyCode", "USD"),
            "timezone": graphql_shop.get("timezoneOffsetMinutes", 0),
            "plan_name": graphql_shop.get("plan", {}).get("displayName", ""),
            "plan_display_name": graphql_shop.get("plan", {}).get("displayName", ""),
            "shopify_plus": graphql_shop.get("plan", {}).get("shopifyPlus", False),
            "created_at": graphql_shop.get("createdAt", ""),
            "updated_at": graphql_shop.get("updatedAt", ""),
            "enabled": graphql_shop.get("enabled", True),
            "setup_required": graphql_shop.get("setupRequired", False),
            "taxes_included": graphql_shop.get("taxesIncluded", False),
            "tax_shipping": graphql_shop.get("taxShipping", False),
            "has_storefront": graphql_shop.get("hasStorefront", False),
            "has_discounts": graphql_shop.get("hasDiscounts", False),
            "has_gift_cards": graphql_shop.get("hasGiftCards", False),
            "multi_location_enabled": graphql_shop.get("multiLocationEnabled", False),
            "checkout_api_supported": graphql_shop.get("checkoutApiSupported", False)
        }
        
        # Convert primary domain
        primary_domain = graphql_shop.get("primaryDomain", {})
        if primary_domain:
            rest_shop["primary_domain"] = {
                "host": primary_domain.get("host", ""),
                "ssl_enabled": primary_domain.get("sslEnabled", False),
                "url": primary_domain.get("url", "")
            }
        
        return rest_shop