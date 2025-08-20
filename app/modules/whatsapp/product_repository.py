from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from .product_models import Product, ProductVariant, ProductImage, ProductSyncStatus
from .whatsapp_models import ShopifyStore
from typing import Optional, List, Dict, Any
import json
from datetime import datetime


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update_product(self, store_id: str, shopify_product: Dict[str, Any]) -> Product:
        """Create or update a product from Shopify data"""
        
        # Check if product already exists
        result = await self.db.execute(
            select(Product).where(
                Product.store_id == store_id,
                Product.shopify_product_id == str(shopify_product["id"])
            ).options(selectinload(Product.variants), selectinload(Product.images))
        )
        product = result.scalar_one_or_none()
        
        if not product:
            # Create new product
            product = Product(
                store_id=store_id,
                shopify_product_id=str(shopify_product["id"]),
                title=shopify_product.get("title", ""),
                description=shopify_product.get("body_html", ""),
                product_type=shopify_product.get("product_type", ""),
                vendor=shopify_product.get("vendor", ""),
                status=shopify_product.get("status", "active"),
                handle=shopify_product.get("handle", ""),
                tags=shopify_product.get("tags", ""),
                shopify_created_at=datetime.fromisoformat(shopify_product["created_at"].replace("Z", "+00:00")).replace(tzinfo=None),
                shopify_updated_at=datetime.fromisoformat(shopify_product["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            )
            self.db.add(product)
            await self.db.flush()  # Get the ID
        else:
            # Update existing product
            product.title = shopify_product.get("title", product.title)
            product.description = shopify_product.get("body_html", product.description)
            product.product_type = shopify_product.get("product_type", product.product_type)
            product.vendor = shopify_product.get("vendor", product.vendor)
            product.status = shopify_product.get("status", product.status)
            product.handle = shopify_product.get("handle", product.handle)
            product.tags = shopify_product.get("tags", product.tags)
            product.shopify_updated_at = datetime.fromisoformat(shopify_product["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
        
        # Handle variants
        if "variants" in shopify_product:
            print(f"[DEBUG] Starting variant sync for product {product.title}")
            print(f"[DEBUG] Shopify provided {len(shopify_product['variants'])} variants")
            await self._sync_variants(product, shopify_product["variants"])
            print(f"[DEBUG] Completed variant sync for product {product.title}")
        
        # Handle images
        if "images" in shopify_product:
            await self._sync_images(product, shopify_product["images"])
        
        # Flush to generate IDs but don't commit yet
        await self.db.flush()
        print(f"[DEBUG] After flush - Product {product.title} has {len(product.variants)} variants in session")
        
        # Now commit the transaction
        await self.db.commit()
        print(f"[DEBUG] Successfully committed product {product.title} with variants")
        return product
    
    async def _sync_variants(self, product: Product, shopify_variants: List[Dict[str, Any]]):
        """Sync product variants"""
        
        # Get existing variants
        existing_variants = {v.shopify_variant_id: v for v in product.variants}
        shopify_variant_ids = {str(v["id"]) for v in shopify_variants}
        
        # Update or create variants
        for variant_data in shopify_variants:
            variant_id = str(variant_data["id"])
            print(f"[DEBUG] Processing variant {variant_id}: price=${variant_data.get('price', 0)}")
            
            if variant_id in existing_variants:
                # Update existing variant
                variant = existing_variants[variant_id]
                variant.title = variant_data.get("title", variant.title)
                variant.price = float(variant_data.get("price", 0))
                variant.compare_at_price = float(variant_data["compare_at_price"]) if variant_data.get("compare_at_price") else None
                variant.sku = variant_data.get("sku", variant.sku)
                variant.inventory_quantity = variant_data.get("inventory_quantity", 0)
                variant.inventory_management = variant_data.get("inventory_management")
                variant.inventory_policy = variant_data.get("inventory_policy", "deny")
                variant.requires_shipping = variant_data.get("requires_shipping", True)
                variant.taxable = variant_data.get("taxable", True)
                variant.weight = float(variant_data["weight"]) if variant_data.get("weight") else None
                variant.weight_unit = variant_data.get("weight_unit", "kg")
                variant.position = variant_data.get("position", 1)
                variant.available = variant_data.get("available", True)
                variant.shopify_updated_at = datetime.fromisoformat(variant_data["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            else:
                # Create new variant
                variant = ProductVariant(
                    product_id=product.id,
                    shopify_variant_id=variant_id,
                    title=variant_data.get("title", "Default"),
                    price=float(variant_data.get("price", 0)),
                    compare_at_price=float(variant_data["compare_at_price"]) if variant_data.get("compare_at_price") else None,
                    sku=variant_data.get("sku"),
                    inventory_quantity=variant_data.get("inventory_quantity", 0),
                    inventory_management=variant_data.get("inventory_management"),
                    inventory_policy=variant_data.get("inventory_policy", "deny"),
                    requires_shipping=variant_data.get("requires_shipping", True),
                    taxable=variant_data.get("taxable", True),
                    weight=float(variant_data["weight"]) if variant_data.get("weight") else None,
                    weight_unit=variant_data.get("weight_unit", "kg"),
                    position=variant_data.get("position", 1),
                    available=variant_data.get("available", True),
                    shopify_created_at=datetime.fromisoformat(variant_data["created_at"].replace("Z", "+00:00")).replace(tzinfo=None),
                    shopify_updated_at=datetime.fromisoformat(variant_data["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                )
                print(f"[DEBUG] Creating new variant: {variant.title} (${variant.price}) for product_id={product.id}")
                self.db.add(variant)
        
        # Delete variants that no longer exist in Shopify
        for existing_id, variant in existing_variants.items():
            if existing_id not in shopify_variant_ids:
                self.db.delete(variant)
    
    async def _sync_images(self, product: Product, shopify_images: List[Dict[str, Any]]):
        """Sync product images"""
        
        # Get existing images
        existing_images = {i.shopify_image_id: i for i in product.images}
        shopify_image_ids = {str(i["id"]) for i in shopify_images}
        
        # Update or create images
        for image_data in shopify_images:
            image_id = str(image_data["id"])
            
            if image_id in existing_images:
                # Update existing image
                image = existing_images[image_id]
                image.image_url = image_data.get("src", image.image_url)
                image.alt_text = image_data.get("alt", image.alt_text)
                image.position = image_data.get("position", image.position)
                image.width = image_data.get("width", image.width)
                image.height = image_data.get("height", image.height)
            else:
                # Create new image
                image = ProductImage(
                    product_id=product.id,
                    shopify_image_id=image_id,
                    image_url=image_data.get("src", ""),
                    alt_text=image_data.get("alt"),
                    position=image_data.get("position", 1),
                    width=image_data.get("width"),
                    height=image_data.get("height")
                )
                self.db.add(image)
        
        # Delete images that no longer exist in Shopify
        for existing_id, image in existing_images.items():
            if existing_id not in shopify_image_ids:
                self.db.delete(image)
    
    async def delete_product(self, store_id: str, shopify_product_id: str):
        """Delete a product by Shopify product ID"""
        result = await self.db.execute(
            select(Product).where(
                Product.store_id == store_id,
                Product.shopify_product_id == shopify_product_id
            )
        )
        product = result.scalar_one_or_none()
        if product:
            self.db.delete(product)
            await self.db.commit()
            print(f"[INFO] Deleted product {shopify_product_id} for store {store_id}")
    
    async def get_products_for_browsing(self, store_id: str, page: int = 1, limit: int = 10, search: str = None) -> Dict[str, Any]:
        """Get products for WhatsApp browsing (from database, not Shopify API)"""
        
        # Try explicit join to force variant loading
        query = select(Product).where(
            Product.store_id == store_id,
            Product.status == "active"
        ).options(
            selectinload(Product.variants),
            selectinload(Product.images)
        )
        
        # Add search filter
        if search:
            query = query.where(Product.title.ilike(f"%{search}%"))
        
        # Add pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        # Force refresh products to load variants from database
        for product in products:
            await self.db.refresh(product, ["variants", "images"])
        
        # Debug: Check if variants are loaded
        for product in products:
            print(f"[DEBUG] Product {product.title}: {len(product.variants)} variants loaded")
            for variant in product.variants:
                print(f"[DEBUG]   - Variant {variant.title}: ${variant.price}")
        
        # Get total count
        count_query = select(Product).where(
            Product.store_id == store_id,
            Product.status == "active"
        )
        if search:
            count_query = count_query.where(Product.title.ilike(f"%{search}%"))
        
        count_result = await self.db.execute(count_query)
        total_count = len(count_result.scalars().all())
        
        return {
            "products": products,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": offset + len(products) < total_count
        }
    
    async def get_product_by_id(self, store_id: str, product_id: str) -> Optional[Product]:
        """Get a specific product by ID"""
        result = await self.db.execute(
            select(Product).where(
                Product.store_id == store_id,
                Product.id == product_id
            ).options(
                selectinload(Product.variants),
                selectinload(Product.images)
            )
        )
        return result.scalar_one_or_none()
    
    async def update_sync_status(self, store_id: str, status: str, total_products: int = None, synced_products: int = None, error_message: str = None):
        """Update product sync status for a store"""
        
        result = await self.db.execute(
            select(ProductSyncStatus).where(ProductSyncStatus.store_id == store_id)
        )
        sync_status = result.scalar_one_or_none()
        
        if not sync_status:
            sync_status = ProductSyncStatus(store_id=store_id)
            self.db.add(sync_status)
        
        sync_status.sync_status = status
        sync_status.last_sync_at = datetime.utcnow()
        
        if total_products is not None:
            sync_status.total_products = total_products
        if synced_products is not None:
            sync_status.synced_products = synced_products
        if error_message is not None:
            sync_status.error_message = error_message
            
        await self.db.commit()
    
    async def get_store_product_count(self, store_id: str) -> int:
        """Get total product count for a store (for health check)"""
        result = await self.db.execute(
            select(Product).where(Product.store_id == store_id)
        )
        return len(result.scalars().all())