import httpx
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .product_repository import ProductRepository
from .whatsapp_repository import ShopifyStoreRepository
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
            
            # Fetch all products from Shopify
            all_products = await self._fetch_all_products(store_url, store.access_token)
            
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
    
    async def _fetch_all_products(self, store_url: str, access_token: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch all products from Shopify API with pagination"""
        
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        all_products = []
        page_info = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                # Build URL with pagination - try different statuses
                url = f"https://{store_url}/admin/api/2024-10/products.json?limit={limit}&status=active"
                if page_info:
                    url += f"&page_info={page_info}"
                
                try:
                    print(f"[DEBUG] API call: {url}")
                    print(f"[DEBUG] Headers: X-Shopify-Access-Token: {access_token[:10]}...")
                    response = await client.get(url, headers=headers)
                    
                    print(f"[DEBUG] Response status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        products = data.get("products", [])
                        print(f"[DEBUG] Raw response products count: {len(products)}")
                        
                        if not products:
                            print("[DEBUG] No products found, breaking loop")
                            break
                        
                        all_products.extend(products)
                        print(f"[INFO] Fetched {len(products)} products (total: {len(all_products)})")
                        
                        # Check for next page
                        link_header = response.headers.get("Link", "")
                        if "rel=\"next\"" in link_header:
                            # Extract page_info from Link header
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
                        # Rate limited - wait and retry
                        print("[WARNING] Rate limited, waiting 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                        
                    else:
                        print(f"[ERROR] Failed to fetch products: {response.status_code}")
                        print(f"[ERROR] Response text: {response.text}")
                        break
                        
                except Exception as e:
                    print(f"[ERROR] Exception while fetching products: {str(e)}")
                    break
                
                # Small delay to be nice to Shopify API
                await asyncio.sleep(0.1)
        
        return all_products
    
    async def sync_single_product(self, store_url: str, shopify_product_id: str) -> Dict[str, Any]:
        """Sync a single product (used by webhooks)"""
        
        store = await self.store_repo.get_store_by_url(store_url)
        if not store or not store.access_token or store.access_token.startswith("UNINSTALLED"):
            return {"status": "error", "message": "Store not found or app uninstalled"}
        
        headers = {
            "X-Shopify-Access-Token": store.access_token,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"https://{store_url}/admin/api/2024-10/products/{shopify_product_id}.json"
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    product_data = response.json().get("product", {})
                    await self.product_repo.create_or_update_product(store.id, product_data)
                    print(f"[INFO] Synced product {shopify_product_id} for store {store_url}")
                    return {"status": "success", "message": "Product synced"}
                
                elif response.status_code == 404:
                    # Product was deleted
                    await self.product_repo.delete_product(store.id, shopify_product_id)
                    return {"status": "success", "message": "Product deleted"}
                
                else:
                    error_msg = f"Failed to fetch product: {response.status_code}"
                    print(f"[ERROR] {error_msg}")
                    return {"status": "error", "message": error_msg}
                    
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
            
            # Get count from Shopify (single API call)
            headers = {
                "X-Shopify-Access-Token": store.access_token,
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://{store_url}/admin/api/2024-10/products/count.json"
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    return {"status": "error", "message": f"Failed to get Shopify count: {response.status_code}"}
                
                shopify_count = response.json().get("count", 0)
            
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