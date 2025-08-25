import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .product_repository import ProductRepository
from .whatsapp_repository import ShopifyStoreRepository
from .shopify_api_adapter import ShopifyAPIAdapter
from typing import Dict, Any, List
from datetime import datetime
from app.core.config import settings


class ProductSyncServiceV2:
    """
    Enhanced Product Sync Service with GraphQL migration support
    Provides backward compatibility while enabling gradual migration to GraphQL
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.store_repo = ShopifyStoreRepository(db)

    def _create_api_adapter(self, store_url: str, access_token: str, use_graphql: bool = None) -> ShopifyAPIAdapter:
        """Create API adapter with configuration"""
        
        # Use parameter if provided, otherwise use global setting
        if use_graphql is None:
            use_graphql = settings.USE_GRAPHQL_API
        
        return ShopifyAPIAdapter(
            store_url=store_url,
            access_token=access_token,
            use_graphql=use_graphql,
            api_version=settings.SHOPIFY_API_VERSION
        )

    async def initial_product_sync(self, store_url: str, use_graphql: bool = None) -> Dict[str, Any]:
        """
        Perform initial product sync when a store first configures WhatsApp
        Can use either REST or GraphQL based on configuration
        """
        print(f"[INFO] Starting initial product sync for store: {store_url}")
        
        # Get store details
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token:
            return {"status": "error", "message": "Store not found or no access token"}
        
        if store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store app is uninstalled"}
        
        # Create API adapter
        api_adapter = self._create_api_adapter(store_url, store.access_token, use_graphql)
        
        try:
            # Update sync status to 'syncing'
            await self.product_repo.update_sync_status(
                store.id, "syncing", total_products=0, synced_products=0
            )
            
            # Log which API is being used
            api_type = "GraphQL" if api_adapter.is_using_graphql() else "REST"
            print(f"[INFO] Using {api_type} API for initial sync of {store_url}")
            
            # Fetch all products using adapter
            all_products = await api_adapter.fetch_all_products()
            
            if not all_products:
                await self.product_repo.update_sync_status(
                    store.id, "completed", total_products=0, synced_products=0
                )
                return {"status": "success", "message": "No products to sync", "synced_count": 0}
            
            # Sync products to database
            synced_count = 0
            total_products = len(all_products)
            
            await self.product_repo.update_sync_status(
                store.id, "syncing", total_products=total_products, synced_products=0
            )
            
            for product_data in all_products:
                try:
                    await self.product_repo.create_or_update_product(store.id, product_data)
                    synced_count += 1
                    
                    # Update progress every 10 products
                    if synced_count % 10 == 0:
                        await self.product_repo.update_sync_status(
                            store.id, "syncing", total_products=total_products, synced_products=synced_count
                        )
                        print(f"[INFO] Synced {synced_count}/{total_products} products for {store_url} via {api_type}")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to sync product {product_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Mark sync as completed
            await self.product_repo.update_sync_status(
                store.id, "completed", total_products=total_products, synced_products=synced_count
            )
            
            print(f"[SUCCESS] Initial sync completed for {store_url} via {api_type}: {synced_count}/{total_products} products")
            
            return {
                "status": "success",
                "message": f"Initial product sync completed via {api_type}",
                "synced_count": synced_count,
                "total_products": total_products,
                "api_used": api_type
            }
            
        except Exception as e:
            error_msg = f"Initial sync failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            await self.product_repo.update_sync_status(
                store.id, "failed", error_message=error_msg
            )
            
            return {"status": "error", "message": error_msg}

    async def sync_single_product(self, store_url: str, shopify_product_id: str, use_graphql: bool = None) -> Dict[str, Any]:
        """Sync a single product (used by webhooks) with API adapter"""
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store not found or app uninstalled"}
        
        # Create API adapter
        api_adapter = self._create_api_adapter(store_url, store.access_token, use_graphql)
        api_type = "GraphQL" if api_adapter.is_using_graphql() else "REST"
        
        try:
            product_data = await api_adapter.fetch_single_product(shopify_product_id)
            
            if product_data is None:
                # Product was deleted
                await self.product_repo.delete_product(store.id, shopify_product_id)
                return {
                    "status": "success", 
                    "message": f"Product deleted (detected via {api_type})",
                    "api_used": api_type
                }
            
            # Update product in database
            await self.product_repo.create_or_update_product(store.id, product_data)
            print(f"[INFO] Synced product {shopify_product_id} for store {store_url} via {api_type}")
            
            return {
                "status": "success",
                "message": f"Product synced via {api_type}",
                "api_used": api_type
            }
                    
        except Exception as e:
            error_msg = f"Exception syncing product via {api_type}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg, "api_used": api_type}

    async def health_check_product_count(self, store_url: str, use_graphql: bool = None) -> Dict[str, Any]:
        """
        Enhanced health check that compares product counts and tests both APIs
        """
        print(f"[INFO] Running enhanced product count health check for store: {store_url}")
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store not found or app uninstalled"}
        
        try:
            # Get count from our database
            db_count = await self.product_repo.get_store_product_count(store.id)
            
            # Create API adapter
            api_adapter = self._create_api_adapter(store_url, store.access_token, use_graphql)
            
            # Get count from Shopify using the configured API
            shopify_count = await api_adapter.get_products_count()
            api_type = "GraphQL" if api_adapter.is_using_graphql() else "REST"
            
            # Calculate mismatch percentage
            if shopify_count == 0:
                mismatch_percent = 0 if db_count == 0 else 100
            else:
                mismatch_percent = abs(db_count - shopify_count) / shopify_count * 100
            
            print(f"[INFO] Health check for {store_url} via {api_type}: DB={db_count}, Shopify={shopify_count}, Mismatch={mismatch_percent:.1f}%")
            
            # Update health check timestamp
            await self.product_repo.update_sync_status(store.id, "healthy")
            
            result = {
                "status": "success",
                "db_count": db_count,
                "shopify_count": shopify_count,
                "mismatch_percent": round(mismatch_percent, 1),
                "action_needed": mismatch_percent > 5,
                "api_used": api_type
            }
            
            # If mismatch > 5%, recommend full sync
            if mismatch_percent > 5:
                print(f"[WARNING] Significant mismatch detected ({mismatch_percent:.1f}%) - consider full sync")
                result["message"] = f"Significant mismatch detected via {api_type} - manual sync recommended"
            else:
                result["message"] = f"Product counts match via {api_type} - no action needed"
            
            return result
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}

    async def compare_apis_health_check(self, store_url: str) -> Dict[str, Any]:
        """
        Compare REST vs GraphQL API responses for migration validation
        """
        print(f"[INFO] Running API comparison health check for store: {store_url}")
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store not found or app uninstalled"}
        
        try:
            # Create API adapter and run health check
            api_adapter = self._create_api_adapter(store_url, store.access_token)
            health_result = await api_adapter.health_check()
            
            # Add database count for comparison
            db_count = await self.product_repo.get_store_product_count(store.id)
            health_result["db_count"] = db_count
            
            # Calculate consistency metrics
            rest_match = abs(db_count - health_result["rest_products_count"]) <= 1
            graphql_match = abs(db_count - health_result["graphql_products_count"]) <= 1
            
            health_result.update({
                "db_rest_match": rest_match,
                "db_graphql_match": graphql_match,
                "apis_consistent": health_result["counts_match"],
                "ready_for_migration": rest_match and graphql_match and health_result["counts_match"]
            })
            
            return {
                "status": "success",
                "health_check": health_result
            }
            
        except Exception as e:
            error_msg = f"API comparison failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}

    async def migrate_store_to_graphql(self, store_url: str) -> Dict[str, Any]:
        """
        Migrate a specific store to GraphQL after validation
        """
        print(f"[INFO] Attempting to migrate store {store_url} to GraphQL")
        
        # First, run comparison health check
        comparison_result = await self.compare_apis_health_check(store_url)
        
        if comparison_result["status"] != "success":
            return {"status": "error", "message": "Health check failed before migration"}
        
        health_data = comparison_result["health_check"]
        
        if not health_data.get("ready_for_migration", False):
            return {
                "status": "error",
                "message": "Store not ready for migration",
                "details": {
                    "apis_consistent": health_data.get("apis_consistent", False),
                    "db_rest_match": health_data.get("db_rest_match", False),
                    "db_graphql_match": health_data.get("db_graphql_match", False)
                }
            }
        
        # Perform test sync with GraphQL
        test_result = await self.sync_single_product(store_url, "test", use_graphql=True)
        
        if test_result["status"] == "success":
            print(f"[SUCCESS] Store {store_url} is ready for GraphQL migration")
            return {
                "status": "success",
                "message": "Store validated and ready for GraphQL migration",
                "health_check": health_data,
                "next_steps": [
                    "Update environment variable USE_GRAPHQL_API=true",
                    "Or call switch_store_api_mode() to enable GraphQL for this store",
                    "Monitor performance and error rates"
                ]
            }
        else:
            return {
                "status": "error",
                "message": "GraphQL test failed",
                "test_result": test_result
            }

    # Backward compatibility methods - delegate to original service if needed
    async def _get_legacy_service(self):
        """Get legacy service for fallback"""
        from .product_sync_service import ProductSyncService
        return ProductSyncService(self.db)