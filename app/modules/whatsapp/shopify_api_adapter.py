import httpx
import asyncio
from typing import Dict, Any, List, Optional
from .shopify_graphql_client import ShopifyGraphQLClient
from datetime import datetime


class ShopifyAPIAdapter:
    """
    Adapter layer that provides a unified interface for both REST and GraphQL APIs
    Allows gradual migration without breaking existing functionality
    """

    def __init__(self, store_url: str, access_token: str, use_graphql: bool = False, api_version: str = "2024-10"):
        self.store_url = store_url
        self.access_token = access_token
        self.use_graphql = use_graphql
        self.api_version = api_version
        
        # Initialize clients
        self.graphql_client = ShopifyGraphQLClient(store_url, access_token, "2025-01")
        self.rest_headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }

    async def fetch_all_products(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch all products using either REST or GraphQL based on configuration
        Returns data in REST format for backward compatibility
        """
        
        if self.use_graphql:
            print(f"[INFO] Fetching products via GraphQL for {self.store_url}")
            return await self._fetch_products_graphql(limit)
        else:
            print(f"[INFO] Fetching products via REST for {self.store_url}")
            return await self._fetch_products_rest(limit)

    async def _fetch_products_graphql(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch products using GraphQL and convert to REST format"""
        
        try:
            graphql_products = await self.graphql_client.get_all_products(limit)
            
            # Convert GraphQL format to REST format for backward compatibility
            rest_format_products = []
            for graphql_product in graphql_products:
                rest_product = self.graphql_client.convert_graphql_to_rest_format(graphql_product)
                rest_format_products.append(rest_product)
            
            print(f"[SUCCESS] Fetched {len(rest_format_products)} products via GraphQL")
            return rest_format_products
            
        except Exception as e:
            print(f"[ERROR] GraphQL product fetch failed: {str(e)}")
            print(f"[INFO] Falling back to REST API")
            return await self._fetch_products_rest(limit)

    async def _fetch_products_rest(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch products using REST API (existing implementation)"""
        
        all_products = []
        page_info = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/products.json?limit={limit}&status=active"
                if page_info:
                    url += f"&page_info={page_info}"
                
                try:
                    print(f"[DEBUG] REST API call: {url}")
                    response = await client.get(url, headers=self.rest_headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        products = data.get("products", [])
                        
                        if not products:
                            break
                        
                        all_products.extend(products)
                        print(f"[INFO] Fetched {len(products)} products via REST (total: {len(all_products)})")
                        
                        # Check for next page
                        link_header = response.headers.get("Link", "")
                        if "rel=\"next\"" in link_header:
                            for link in link_header.split(","):
                                if "rel=\"next\"" in link:
                                    next_url = link.split(";")[0].strip("<>")
                                    if "page_info=" in next_url:
                                        page_info = next_url.split("page_info=")[1].split("&")[0]
                                    break
                            else:
                                break
                        else:
                            break
                    
                    elif response.status_code == 429:
                        print("[WARNING] REST API rate limited, waiting 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                        
                    else:
                        print(f"[ERROR] REST API failed: {response.status_code}")
                        print(f"[ERROR] Response: {response.text}")
                        break
                        
                except Exception as e:
                    print(f"[ERROR] REST API exception: {str(e)}")
                    break
                
                await asyncio.sleep(0.1)
        
        return all_products

    async def fetch_single_product(self, shopify_product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single product by ID using either REST or GraphQL
        Returns data in REST format for backward compatibility
        """
        
        if self.use_graphql:
            print(f"[INFO] Fetching single product via GraphQL: {shopify_product_id}")
            return await self._fetch_single_product_graphql(shopify_product_id)
        else:
            print(f"[INFO] Fetching single product via REST: {shopify_product_id}")
            return await self._fetch_single_product_rest(shopify_product_id)

    async def _fetch_single_product_graphql(self, shopify_product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single product using GraphQL"""
        
        try:
            result = await self.graphql_client.get_product_by_id(shopify_product_id)
            
            if "error" in result:
                if result["error"] == "rate_limited":
                    print("[WARNING] GraphQL rate limited for single product, waiting...")
                    await asyncio.sleep(2)
                    return await self._fetch_single_product_graphql(shopify_product_id)
                else:
                    print(f"[ERROR] GraphQL single product fetch failed: {result}")
                    return await self._fetch_single_product_rest(shopify_product_id)
            
            product = result.get("product")
            if not product:
                return None
            
            # Convert to REST format
            rest_product = self.graphql_client.convert_graphql_to_rest_format(product)
            print(f"[SUCCESS] Fetched single product via GraphQL: {shopify_product_id}")
            return rest_product
            
        except Exception as e:
            print(f"[ERROR] GraphQL single product exception: {str(e)}")
            print(f"[INFO] Falling back to REST API")
            return await self._fetch_single_product_rest(shopify_product_id)

    async def _fetch_single_product_rest(self, shopify_product_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single product using REST API"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/products/{shopify_product_id}.json"
                response = await client.get(url, headers=self.rest_headers)
                
                if response.status_code == 200:
                    product_data = response.json().get("product", {})
                    print(f"[SUCCESS] Fetched single product via REST: {shopify_product_id}")
                    return product_data
                
                elif response.status_code == 404:
                    print(f"[INFO] Product not found via REST: {shopify_product_id}")
                    return None
                
                else:
                    print(f"[ERROR] REST single product failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST single product exception: {str(e)}")
                return None

    async def get_products_count(self) -> int:
        """
        Get total products count using either REST or GraphQL
        """
        
        if self.use_graphql:
            print(f"[INFO] Getting products count via GraphQL for {self.store_url}")
            return await self._get_products_count_graphql()
        else:
            print(f"[INFO] Getting products count via REST for {self.store_url}")
            return await self._get_products_count_rest()

    async def _get_products_count_graphql(self) -> int:
        """Get products count using GraphQL"""
        
        try:
            result = await self.graphql_client.get_products_count()
            
            if "error" in result:
                print(f"[ERROR] GraphQL count failed: {result}")
                print(f"[INFO] Falling back to REST API")
                return await self._get_products_count_rest()
            
            count = result.get("products", {}).get("totalCount", 0)
            print(f"[SUCCESS] Got products count via GraphQL: {count}")
            return count
            
        except Exception as e:
            print(f"[ERROR] GraphQL count exception: {str(e)}")
            print(f"[INFO] Falling back to REST API")
            return await self._get_products_count_rest()

    async def _get_products_count_rest(self) -> int:
        """Get products count using REST API"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/products/count.json"
                response = await client.get(url, headers=self.rest_headers)
                
                if response.status_code == 200:
                    count = response.json().get("count", 0)
                    print(f"[SUCCESS] Got products count via REST: {count}")
                    return count
                else:
                    print(f"[ERROR] REST count failed: {response.status_code}")
                    return 0
                    
            except Exception as e:
                print(f"[ERROR] REST count exception: {str(e)}")
                return 0

    def switch_to_graphql(self):
        """Switch to using GraphQL API"""
        self.use_graphql = True
        print(f"[INFO] Switched to GraphQL API for {self.store_url}")

    def switch_to_rest(self):
        """Switch to using REST API"""
        self.use_graphql = False
        print(f"[INFO] Switched to REST API for {self.store_url}")

    def is_using_graphql(self) -> bool:
        """Check if currently using GraphQL"""
        return self.use_graphql

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on both APIs to compare functionality
        """
        
        print(f"[INFO] Running API health check for {self.store_url}")
        
        # Test both APIs
        rest_count = await self._get_products_count_rest()
        graphql_count = await self._get_products_count_graphql()
        
        # Test single product fetch (use first available product)
        rest_products = []
        graphql_products = []
        
        try:
            # Get a small sample from both APIs
            original_mode = self.use_graphql
            
            self.use_graphql = False
            rest_sample = await self.fetch_all_products(limit=5)
            rest_products = len(rest_sample)
            
            self.use_graphql = True
            graphql_sample = await self.fetch_all_products(limit=5)
            graphql_products = len(graphql_sample)
            
            # Restore original mode
            self.use_graphql = original_mode
            
        except Exception as e:
            print(f"[ERROR] Health check exception: {str(e)}")
        
        health_result = {
            "store_url": self.store_url,
            "rest_products_count": rest_count,
            "graphql_products_count": graphql_count,
            "rest_sample_size": rest_products,
            "graphql_sample_size": graphql_products,
            "counts_match": rest_count == graphql_count,
            "samples_match": rest_products == graphql_products,
            "currently_using": "GraphQL" if self.use_graphql else "REST",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"[INFO] Health check results: {health_result}")
        return health_result

    # ============================================================================
    # ORDERS API Methods
    # ============================================================================

    async def fetch_orders(self, limit: int = 50, query: str = "") -> List[Dict[str, Any]]:
        """Fetch orders using either REST or GraphQL based on configuration"""
        
        if self.use_graphql:
            print(f"[INFO] Fetching orders via GraphQL for {self.store_url}")
            return await self._fetch_orders_graphql(limit, query)
        else:
            print(f"[INFO] Fetching orders via REST for {self.store_url}")
            return await self._fetch_orders_rest(limit, query)

    async def _fetch_orders_graphql(self, limit: int = 50, query: str = "") -> List[Dict[str, Any]]:
        """Fetch orders using GraphQL"""
        
        try:
            result = await self.graphql_client.get_orders(first=limit, query=query)
            
            if "error" in result:
                print(f"[ERROR] GraphQL orders fetch failed: {result}")
                return await self._fetch_orders_rest(limit, query)
            
            # Convert GraphQL format to REST format
            orders_data = result.get("orders", {})
            edges = orders_data.get("edges", [])
            
            rest_format_orders = []
            for edge in edges:
                order_node = edge.get("node", {})
                rest_order = self.graphql_client.convert_order_graphql_to_rest(order_node)
                rest_format_orders.append(rest_order)
            
            print(f"[SUCCESS] Fetched {len(rest_format_orders)} orders via GraphQL")
            return rest_format_orders
            
        except Exception as e:
            print(f"[ERROR] GraphQL orders fetch exception: {str(e)}")
            return await self._fetch_orders_rest(limit, query)

    async def _fetch_orders_rest(self, limit: int = 50, query: str = "") -> List[Dict[str, Any]]:
        """Fetch orders using REST API"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                params = {"limit": limit}
                if query:
                    params["status"] = query  # For REST, query is typically status
                
                url = f"https://{self.store_url}/admin/api/{self.api_version}/orders.json"
                response = await client.get(url, headers=self.rest_headers, params=params)
                
                if response.status_code == 200:
                    orders = response.json().get("orders", [])
                    print(f"[SUCCESS] Fetched {len(orders)} orders via REST")
                    return orders
                else:
                    print(f"[ERROR] REST orders fetch failed: {response.status_code}")
                    return []
                    
            except Exception as e:
                print(f"[ERROR] REST orders fetch exception: {str(e)}")
                return []

    async def fetch_single_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single order by ID"""
        
        if self.use_graphql:
            return await self._fetch_single_order_graphql(order_id)
        else:
            return await self._fetch_single_order_rest(order_id)

    async def _fetch_single_order_graphql(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single order using GraphQL"""
        
        try:
            result = await self.graphql_client.get_order_by_id(order_id)
            
            if "error" in result:
                return await self._fetch_single_order_rest(order_id)
            
            order = result.get("order")
            if not order:
                return None
            
            return self.graphql_client.convert_order_graphql_to_rest(order)
            
        except Exception as e:
            print(f"[ERROR] GraphQL single order exception: {str(e)}")
            return await self._fetch_single_order_rest(order_id)

    async def _fetch_single_order_rest(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single order using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/orders/{order_id}.json"
                response = await client.get(url, headers=self.rest_headers)
                
                if response.status_code == 200:
                    return response.json().get("order", {})
                else:
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST single order exception: {str(e)}")
                return None

    # ============================================================================
    # CUSTOMERS API Methods
    # ============================================================================

    async def fetch_customers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch customers using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._fetch_customers_graphql(limit)
        else:
            return await self._fetch_customers_rest(limit)

    async def _fetch_customers_graphql(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch customers using GraphQL"""
        
        try:
            result = await self.graphql_client.get_customers(first=limit)
            
            if "error" in result:
                return await self._fetch_customers_rest(limit)
            
            customers_data = result.get("customers", {})
            edges = customers_data.get("edges", [])
            
            rest_format_customers = []
            for edge in edges:
                customer_node = edge.get("node", {})
                rest_customer = self.graphql_client.convert_customer_graphql_to_rest(customer_node)
                rest_format_customers.append(rest_customer)
            
            return rest_format_customers
            
        except Exception as e:
            print(f"[ERROR] GraphQL customers fetch exception: {str(e)}")
            return await self._fetch_customers_rest(limit)

    async def _fetch_customers_rest(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch customers using REST"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/customers.json"
                params = {"limit": limit}
                response = await client.get(url, headers=self.rest_headers, params=params)
                
                if response.status_code == 200:
                    return response.json().get("customers", [])
                else:
                    return []
                    
            except Exception as e:
                print(f"[ERROR] REST customers fetch exception: {str(e)}")
                return []

    async def create_customer(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a customer using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._create_customer_graphql(customer_data)
        else:
            return await self._create_customer_rest(customer_data)

    async def _create_customer_graphql(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create customer using GraphQL"""
        
        try:
            result = await self.graphql_client.create_customer(customer_data)
            
            if "error" in result:
                return await self._create_customer_rest(customer_data)
            
            customer_result = result.get("customerCreate", {})
            if customer_result.get("userErrors"):
                print(f"[ERROR] GraphQL customer creation errors: {customer_result['userErrors']}")
                return None
            
            customer = customer_result.get("customer", {})
            if customer:
                return self.graphql_client.convert_customer_graphql_to_rest(customer)
            
            return None
            
        except Exception as e:
            print(f"[ERROR] GraphQL customer creation exception: {str(e)}")
            return await self._create_customer_rest(customer_data)

    async def _create_customer_rest(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create customer using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/customers.json"
                payload = {"customer": customer_data}
                response = await client.post(url, headers=self.rest_headers, json=payload)
                
                if response.status_code == 201:
                    return response.json().get("customer", {})
                else:
                    print(f"[ERROR] REST customer creation failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST customer creation exception: {str(e)}")
                return None

    # ============================================================================
    # DRAFT ORDERS API Methods
    # ============================================================================

    async def create_draft_order(self, draft_order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a draft order using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._create_draft_order_graphql(draft_order_data)
        else:
            return await self._create_draft_order_rest(draft_order_data)

    async def _create_draft_order_graphql(self, draft_order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create draft order using GraphQL"""
        
        try:
            result = await self.graphql_client.create_draft_order(draft_order_data)
            
            if "error" in result:
                return await self._create_draft_order_rest(draft_order_data)
            
            draft_order_result = result.get("draftOrderCreate", {})
            if draft_order_result.get("userErrors"):
                print(f"[ERROR] GraphQL draft order creation errors: {draft_order_result['userErrors']}")
                return None
            
            draft_order = draft_order_result.get("draftOrder", {})
            if draft_order:
                # Convert to REST format for compatibility
                return {
                    "id": int(draft_order.get("legacyResourceId", 0)),
                    "name": draft_order.get("name", ""),
                    "email": draft_order.get("email", ""),
                    "invoice_url": draft_order.get("invoiceUrl", ""),
                    "status": draft_order.get("status", ""),
                    "total_price": draft_order.get("totalPriceSet", {}).get("shopMoney", {}).get("amount", "0.00"),
                    "created_at": draft_order.get("createdAt", ""),
                    "admin_graphql_api_id": draft_order.get("id", "")
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] GraphQL draft order creation exception: {str(e)}")
            return await self._create_draft_order_rest(draft_order_data)

    async def _create_draft_order_rest(self, draft_order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create draft order using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/draft_orders.json"
                payload = {"draft_order": draft_order_data}
                response = await client.post(url, headers=self.rest_headers, json=payload)
                
                if response.status_code == 201:
                    return response.json().get("draft_order", {})
                else:
                    print(f"[ERROR] REST draft order creation failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST draft order creation exception: {str(e)}")
                return None

    async def complete_draft_order(self, draft_order_id: str) -> Optional[Dict[str, Any]]:
        """Complete a draft order using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._complete_draft_order_graphql(draft_order_id)
        else:
            return await self._complete_draft_order_rest(draft_order_id)

    async def _complete_draft_order_graphql(self, draft_order_id: str) -> Optional[Dict[str, Any]]:
        """Complete draft order using GraphQL"""
        
        try:
            result = await self.graphql_client.complete_draft_order(draft_order_id)
            
            if "error" in result:
                return await self._complete_draft_order_rest(draft_order_id)
            
            completion_result = result.get("draftOrderComplete", {})
            if completion_result.get("userErrors"):
                print(f"[ERROR] GraphQL draft order completion errors: {completion_result['userErrors']}")
                return None
            
            order = completion_result.get("order", {})
            if order:
                return {
                    "id": int(order.get("legacyResourceId", 0)),
                    "name": order.get("name", ""),
                    "admin_graphql_api_id": order.get("id", "")
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] GraphQL draft order completion exception: {str(e)}")
            return await self._complete_draft_order_rest(draft_order_id)

    async def _complete_draft_order_rest(self, draft_order_id: str) -> Optional[Dict[str, Any]]:
        """Complete draft order using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/draft_orders/{draft_order_id}/complete.json"
                response = await client.put(url, headers=self.rest_headers)
                
                if response.status_code == 200:
                    return response.json().get("draft_order", {})
                else:
                    print(f"[ERROR] REST draft order completion failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST draft order completion exception: {str(e)}")
                return None

    # ============================================================================
    # SHOP INFO API Methods
    # ============================================================================

    async def get_shop_info(self) -> Optional[Dict[str, Any]]:
        """Get shop information using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._get_shop_info_graphql()
        else:
            return await self._get_shop_info_rest()

    async def _get_shop_info_graphql(self) -> Optional[Dict[str, Any]]:
        """Get shop info using GraphQL"""
        
        try:
            result = await self.graphql_client.get_shop_info()
            
            if "error" in result:
                return await self._get_shop_info_rest()
            
            shop = result.get("shop", {})
            if shop:
                return self.graphql_client.convert_shop_graphql_to_rest(shop)
            
            return None
            
        except Exception as e:
            print(f"[ERROR] GraphQL shop info exception: {str(e)}")
            return await self._get_shop_info_rest()

    async def _get_shop_info_rest(self) -> Optional[Dict[str, Any]]:
        """Get shop info using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/shop.json"
                response = await client.get(url, headers=self.rest_headers)
                
                if response.status_code == 200:
                    return response.json().get("shop", {})
                else:
                    print(f"[ERROR] REST shop info failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST shop info exception: {str(e)}")
                return None

    # ============================================================================
    # WEBHOOKS API Methods
    # ============================================================================

    async def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get webhooks using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._get_webhooks_graphql()
        else:
            return await self._get_webhooks_rest()

    async def _get_webhooks_graphql(self) -> List[Dict[str, Any]]:
        """Get webhooks using GraphQL"""
        
        try:
            result = await self.graphql_client.get_webhooks()
            
            if "error" in result:
                return await self._get_webhooks_rest()
            
            webhooks_data = result.get("webhookSubscriptions", {})
            edges = webhooks_data.get("edges", [])
            
            rest_format_webhooks = []
            for edge in edges:
                webhook_node = edge.get("node", {})
                rest_webhook = {
                    "id": int(webhook_node.get("legacyResourceId", 0)),
                    "address": webhook_node.get("callbackUrl", ""),
                    "topic": webhook_node.get("topic", ""),
                    "format": webhook_node.get("format", "json"),
                    "created_at": webhook_node.get("createdAt", ""),
                    "updated_at": webhook_node.get("updatedAt", ""),
                    "admin_graphql_api_id": webhook_node.get("id", "")
                }
                rest_format_webhooks.append(rest_webhook)
            
            return rest_format_webhooks
            
        except Exception as e:
            print(f"[ERROR] GraphQL webhooks fetch exception: {str(e)}")
            return await self._get_webhooks_rest()

    async def _get_webhooks_rest(self) -> List[Dict[str, Any]]:
        """Get webhooks using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/webhooks.json"
                response = await client.get(url, headers=self.rest_headers)
                
                if response.status_code == 200:
                    return response.json().get("webhooks", [])
                else:
                    print(f"[ERROR] REST webhooks fetch failed: {response.status_code}")
                    return []
                    
            except Exception as e:
                print(f"[ERROR] REST webhooks fetch exception: {str(e)}")
                return []

    async def create_webhook(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a webhook using either REST or GraphQL"""
        
        if self.use_graphql:
            return await self._create_webhook_graphql(webhook_data)
        else:
            return await self._create_webhook_rest(webhook_data)

    async def _create_webhook_graphql(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create webhook using GraphQL"""
        
        try:
            result = await self.graphql_client.create_webhook(webhook_data)
            
            if "error" in result:
                return await self._create_webhook_rest(webhook_data)
            
            webhook_result = result.get("webhookSubscriptionCreate", {})
            if webhook_result.get("userErrors"):
                print(f"[ERROR] GraphQL webhook creation errors: {webhook_result['userErrors']}")
                return None
            
            webhook = webhook_result.get("webhookSubscription", {})
            if webhook:
                return {
                    "id": int(webhook.get("legacyResourceId", 0)),
                    "address": webhook.get("callbackUrl", ""),
                    "topic": webhook.get("topic", ""),
                    "format": webhook.get("format", "json"),
                    "created_at": webhook.get("createdAt", ""),
                    "admin_graphql_api_id": webhook.get("id", "")
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] GraphQL webhook creation exception: {str(e)}")
            return await self._create_webhook_rest(webhook_data)

    async def _create_webhook_rest(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create webhook using REST"""
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{self.store_url}/admin/api/{self.api_version}/webhooks.json"
                payload = {"webhook": webhook_data}
                response = await client.post(url, headers=self.rest_headers, json=payload)
                
                if response.status_code == 201:
                    return response.json().get("webhook", {})
                else:
                    print(f"[ERROR] REST webhook creation failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"[ERROR] REST webhook creation exception: {str(e)}")
                return None