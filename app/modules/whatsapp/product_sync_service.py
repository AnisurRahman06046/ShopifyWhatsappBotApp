import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .product_repository import ProductRepository
from .whatsapp_repository import ShopifyStoreRepository
from .shopify_api_adapter import ShopifyAPIAdapter
from typing import Dict, Any, List
from datetime import datetime


class ProductSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.store_repo = ShopifyStoreRepository(db)

    async def initial_product_sync(self, store_url: str) -> Dict[str, Any]:
        """
        Perform initial product sync when a store first configures WhatsApp
        This is the ONLY time we do a full product sync
        """
        print(f"[INFO] Starting initial product sync for store: {store_url}")
        
        # Get store details
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token:
            return {"status": "error", "message": "Store not found or no access token"}
        
        if store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store app is uninstalled"}
        
        try:
            # Update sync status to 'syncing'
            await self.product_repo.update_sync_status(
                store.id, "syncing", total_products=0, synced_products=0
            )
            
            # Fetch all products from Shopify using GraphQL
            api_adapter = ShopifyAPIAdapter(store_url, store.access_token, use_graphql=True)
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
                        print(f"[INFO] Synced {synced_count}/{total_products} products for {store_url}")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to sync product {product_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Mark sync as completed
            await self.product_repo.update_sync_status(
                store.id, "completed", total_products=total_products, synced_products=synced_count
            )
            
            print(f"[SUCCESS] Initial sync completed for {store_url}: {synced_count}/{total_products} products")
            
            return {
                "status": "success",
                "message": "Initial product sync completed",
                "synced_count": synced_count,
                "total_products": total_products
            }
            
        except Exception as e:
            error_msg = f"Initial sync failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            
            await self.product_repo.update_sync_status(
                store.id, "failed", error_message=error_msg
            )
            
            return {"status": "error", "message": error_msg}
    
    # REST API method removed - now using GraphQL via adapter
    
    async def sync_single_product(self, store_url: str, shopify_product_id: str) -> Dict[str, Any]:
        """Sync a single product (used by webhooks)"""
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store not found or app uninstalled"}
        
        try:
            # Use GraphQL API via adapter
            api_adapter = ShopifyAPIAdapter(store_url, store.access_token, use_graphql=True)
            product_data = await api_adapter.fetch_single_product(shopify_product_id)
            
            if product_data:
                await self.product_repo.create_or_update_product(store.id, product_data)
                print(f"[INFO] Synced product {shopify_product_id} for store {store_url}")
                return {"status": "success", "message": "Product synced"}
            else:
                # Product was deleted or not found
                await self.product_repo.delete_product(store.id, shopify_product_id)
                return {"status": "success", "message": "Product deleted"}
                
        except Exception as e:
            error_msg = f"Exception syncing product: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}
    
    async def health_check_product_count(self, store_url: str) -> Dict[str, Any]:
        """
        Weekly health check: Compare product count in DB vs Shopify
        If mismatch > 5%, trigger one-time sync
        """
        print(f"[INFO] Running product count health check for store: {store_url}")
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store not found or app uninstalled"}
        
        try:
            # Get count from our database
            db_count = await self.product_repo.get_store_product_count(store.id)
            
            # Get count from Shopify using GraphQL API
            api_adapter = ShopifyAPIAdapter(store_url, store.access_token, use_graphql=True)
            shopify_count = await api_adapter.get_products_count()
            
            # Calculate mismatch percentage
            if shopify_count == 0:
                mismatch_percent = 0 if db_count == 0 else 100
            else:
                mismatch_percent = abs(db_count - shopify_count) / shopify_count * 100
            
            print(f"[INFO] Health check for {store_url}: DB={db_count}, Shopify={shopify_count}, Mismatch={mismatch_percent:.1f}%")
            
            # Update health check timestamp
            await self.product_repo.update_sync_status(store.id, "healthy")
            
            result = {
                "status": "success",
                "db_count": db_count,
                "shopify_count": shopify_count,
                "mismatch_percent": round(mismatch_percent, 1),
                "action_needed": mismatch_percent > 5
            }
            
            # If mismatch > 5%, recommend full sync
            if mismatch_percent > 5:
                print(f"[WARNING] Significant mismatch detected ({mismatch_percent:.1f}%) - consider full sync")
                result["message"] = "Significant mismatch detected - manual sync recommended"
            else:
                result["message"] = "Product counts match - no action needed"
            
            return result
            
        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"status": "error", "message": error_msg}