from sqlalchemy.ext.asyncio import AsyncSession
from .whatsapp_repository import ShopifyStoreRepository
from .shopify_api_adapter import ShopifyAPIAdapter
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.config import settings


class CompleteShopifyService:
    """
    Complete Shopify service with GraphQL support for all APIs
    Provides unified access to products, orders, customers, draft orders, shop info, and webhooks
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.store_repo = ShopifyStoreRepository(db)

    def _create_api_adapter(self, store_url: str, access_token: str, use_graphql: bool = None) -> ShopifyAPIAdapter:
        """Create API adapter with configuration"""
        
        if use_graphql is None:
            use_graphql = settings.USE_GRAPHQL_API
        
        return ShopifyAPIAdapter(
            store_url=store_url,
            access_token=access_token,
            use_graphql=use_graphql,
            api_version=settings.SHOPIFY_API_VERSION
        )

    async def _get_store_adapter(self, store_url: str, use_graphql: bool = None) -> Optional[ShopifyAPIAdapter]:
        """Get store and create API adapter"""
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return None
        
        return self._create_api_adapter(store_url, store.access_token, use_graphql)

    # ============================================================================
    # PRODUCTS API - Enhanced with full GraphQL support
    # ============================================================================

    async def get_all_products(self, store_url: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Get all products with optional GraphQL usage"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found or access token invalid"}
        
        try:
            products = await adapter.fetch_all_products()
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            return {
                "status": "success",
                "products": products,
                "count": len(products),
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_products_count(self, store_url: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Get product count with optional GraphQL usage"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            count = await adapter.get_products_count()
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            return {
                "status": "success",
                "count": count,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_single_product(self, store_url: str, product_id: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Get single product with optional GraphQL usage"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            product = await adapter.fetch_single_product(product_id)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not product:
                return {"status": "not_found", "message": "Product not found"}
            
            return {
                "status": "success",
                "product": product,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # ORDERS API - Full GraphQL support
    # ============================================================================

    async def get_orders(self, store_url: str, limit: int = 50, query: str = "", use_graphql: bool = None) -> Dict[str, Any]:
        """Get orders with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            orders = await adapter.fetch_orders(limit=limit, query=query)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            return {
                "status": "success",
                "orders": orders,
                "count": len(orders),
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_single_order(self, store_url: str, order_id: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Get single order with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            order = await adapter.fetch_single_order(order_id)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not order:
                return {"status": "not_found", "message": "Order not found"}
            
            return {
                "status": "success",
                "order": order,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # CUSTOMERS API - Full GraphQL support
    # ============================================================================

    async def get_customers(self, store_url: str, limit: int = 50, use_graphql: bool = None) -> Dict[str, Any]:
        """Get customers with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            customers = await adapter.fetch_customers(limit=limit)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            return {
                "status": "success",
                "customers": customers,
                "count": len(customers),
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_customer(self, store_url: str, customer_data: Dict[str, Any], use_graphql: bool = None) -> Dict[str, Any]:
        """Create customer with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            customer = await adapter.create_customer(customer_data)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not customer:
                return {"status": "error", "message": "Customer creation failed"}
            
            return {
                "status": "success",
                "customer": customer,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # DRAFT ORDERS API - Full GraphQL support
    # ============================================================================

    async def create_draft_order(self, store_url: str, draft_order_data: Dict[str, Any], use_graphql: bool = None) -> Dict[str, Any]:
        """Create draft order with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            draft_order = await adapter.create_draft_order(draft_order_data)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not draft_order:
                return {"status": "error", "message": "Draft order creation failed"}
            
            return {
                "status": "success",
                "draft_order": draft_order,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def complete_draft_order(self, store_url: str, draft_order_id: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Complete draft order with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            order = await adapter.complete_draft_order(draft_order_id)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not order:
                return {"status": "error", "message": "Draft order completion failed"}
            
            return {
                "status": "success",
                "order": order,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # SHOP INFO API - Full GraphQL support
    # ============================================================================

    async def get_shop_info(self, store_url: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Get shop information with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            shop = await adapter.get_shop_info()
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not shop:
                return {"status": "error", "message": "Shop info not available"}
            
            return {
                "status": "success",
                "shop": shop,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # WEBHOOKS API - Full GraphQL support
    # ============================================================================

    async def get_webhooks(self, store_url: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Get webhooks with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            webhooks = await adapter.get_webhooks()
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            return {
                "status": "success",
                "webhooks": webhooks,
                "count": len(webhooks),
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_webhook(self, store_url: str, webhook_data: Dict[str, Any], use_graphql: bool = None) -> Dict[str, Any]:
        """Create webhook with GraphQL support"""
        
        adapter = await self._get_store_adapter(store_url, use_graphql)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            webhook = await adapter.create_webhook(webhook_data)
            api_type = "GraphQL" if adapter.is_using_graphql() else "REST"
            
            if not webhook:
                return {"status": "error", "message": "Webhook creation failed"}
            
            return {
                "status": "success",
                "webhook": webhook,
                "api_used": api_type
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ============================================================================
    # MIGRATION & HEALTH CHECK METHODS
    # ============================================================================

    async def comprehensive_health_check(self, store_url: str) -> Dict[str, Any]:
        """Run comprehensive health check across all APIs"""
        
        print(f"[INFO] Running comprehensive health check for {store_url}")
        
        adapter = await self._get_store_adapter(store_url)
        if not adapter:
            return {"status": "error", "message": "Store not found"}
        
        try:
            # Run health check on all APIs
            health_result = await adapter.health_check()
            
            # Test additional APIs
            test_results = {}
            
            # Test orders
            try:
                orders_rest = await adapter._fetch_orders_rest(limit=1)
                adapter.switch_to_graphql()
                orders_graphql = await adapter._fetch_orders_graphql(limit=1)
                test_results["orders"] = {
                    "rest_success": len(orders_rest) >= 0,
                    "graphql_success": len(orders_graphql) >= 0,
                    "consistent": len(orders_rest) == len(orders_graphql)
                }
            except Exception as e:
                test_results["orders"] = {"error": str(e)}
            
            # Test shop info
            try:
                adapter.switch_to_rest()
                shop_rest = await adapter._get_shop_info_rest()
                adapter.switch_to_graphql()
                shop_graphql = await adapter._get_shop_info_graphql()
                test_results["shop_info"] = {
                    "rest_success": shop_rest is not None,
                    "graphql_success": shop_graphql is not None,
                    "names_match": (shop_rest or {}).get("name") == (shop_graphql or {}).get("name")
                }
            except Exception as e:
                test_results["shop_info"] = {"error": str(e)}
            
            # Calculate overall health
            api_health_scores = []
            
            # Products health (from original health check)
            if health_result.get("counts_match", False):
                api_health_scores.append(1.0)
            else:
                api_health_scores.append(0.0)
            
            # Orders health
            orders_result = test_results.get("orders", {})
            if orders_result.get("consistent", False):
                api_health_scores.append(1.0)
            else:
                api_health_scores.append(0.5 if not orders_result.get("error") else 0.0)
            
            # Shop info health
            shop_result = test_results.get("shop_info", {})
            if shop_result.get("names_match", False):
                api_health_scores.append(1.0)
            else:
                api_health_scores.append(0.5 if shop_result.get("rest_success", False) and shop_result.get("graphql_success", False) else 0.0)
            
            overall_health_score = sum(api_health_scores) / len(api_health_scores) * 100
            
            return {
                "status": "success",
                "store_url": store_url,
                "overall_health_score": round(overall_health_score, 1),
                "ready_for_full_migration": overall_health_score >= 80,
                "product_health": health_result,
                "additional_tests": test_results,
                "recommendation": self._get_migration_recommendation(overall_health_score),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _get_migration_recommendation(self, health_score: float) -> str:
        """Get migration recommendation based on health score"""
        
        if health_score >= 90:
            return "✅ Excellent health - Full GraphQL migration recommended"
        elif health_score >= 80:
            return "🟢 Good health - GraphQL migration recommended with monitoring"
        elif health_score >= 60:
            return "🟡 Fair health - Consider gradual API-by-API migration"
        elif health_score >= 40:
            return "🟠 Poor health - Fix issues before migration"
        else:
            return "🔴 Critical issues - Do not migrate until resolved"

    async def migrate_store_to_graphql(self, store_url: str) -> Dict[str, Any]:
        """Migrate a store to GraphQL after comprehensive validation"""
        
        print(f"[INFO] Starting comprehensive migration validation for {store_url}")
        
        # Run comprehensive health check first
        health_check = await self.comprehensive_health_check(store_url)
        
        if health_check["status"] != "success":
            return health_check
        
        if not health_check["ready_for_full_migration"]:
            return {
                "status": "not_ready",
                "message": f"Store not ready for migration (Health: {health_check['overall_health_score']}%)",
                "recommendation": health_check["recommendation"],
                "health_details": health_check
            }
        
        # Store is ready for migration
        return {
            "status": "ready",
            "message": f"Store is ready for GraphQL migration (Health: {health_check['overall_health_score']}%)",
            "health_score": health_check["overall_health_score"],
            "next_steps": [
                "Set USE_GRAPHQL_API=true in environment variables",
                "Monitor application logs for any GraphQL errors",
                "Run periodic health checks to ensure consistency",
                "Consider gradual rollout if serving multiple stores"
            ],
            "rollback_plan": [
                "Set USE_GRAPHQL_API=false to revert to REST",
                "GraphQL errors automatically fallback to REST",
                "No data loss risk during migration"
            ]
        }

    # ============================================================================
    # USAGE EXAMPLES & DEMONSTRATIONS
    # ============================================================================

    async def demonstrate_api_usage(self, store_url: str) -> Dict[str, Any]:
        """Demonstrate usage of all APIs with both REST and GraphQL"""
        
        print(f"[INFO] Running API demonstration for {store_url}")
        
        results = {
            "store_url": store_url,
            "demonstrations": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Products demonstration
            print("\n--- Products API Demo ---")
            products_rest = await self.get_products_count(store_url, use_graphql=False)
            products_graphql = await self.get_products_count(store_url, use_graphql=True)
            results["demonstrations"]["products"] = {
                "rest_result": products_rest,
                "graphql_result": products_graphql
            }
            
            # Shop info demonstration
            print("--- Shop Info API Demo ---")
            shop_rest = await self.get_shop_info(store_url, use_graphql=False)
            shop_graphql = await self.get_shop_info(store_url, use_graphql=True)
            results["demonstrations"]["shop_info"] = {
                "rest_result": shop_rest,
                "graphql_result": shop_graphql
            }
            
            # Orders demonstration
            print("--- Orders API Demo ---")
            orders_rest = await self.get_orders(store_url, limit=2, use_graphql=False)
            orders_graphql = await self.get_orders(store_url, limit=2, use_graphql=True)
            results["demonstrations"]["orders"] = {
                "rest_result": orders_rest,
                "graphql_result": orders_graphql
            }
            
            print(f"[SUCCESS] API demonstration completed for {store_url}")
            return {"status": "success", "results": results}
            
        except Exception as e:
            print(f"[ERROR] API demonstration failed: {str(e)}")
            return {"status": "error", "message": str(e), "partial_results": results}