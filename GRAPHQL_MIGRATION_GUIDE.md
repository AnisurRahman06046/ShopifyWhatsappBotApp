# GraphQL Migration Guide

## Overview

This guide provides a safe migration path from Shopify's deprecated REST Admin API to the GraphQL Admin API without breaking existing functionality.

## Why Migrate?

- **Deprecated REST API**: Shopify's `/products` and `/variants` REST endpoints are deprecated as of 2024-04
- **Better Performance**: GraphQL allows fetching related data in a single request
- **Future-proof**: GraphQL is Shopify's recommended approach going forward
- **Efficiency**: Request only the data you need

## Migration Strategy

### Phase 1: Testing & Validation ✅ COMPLETED

1. **GraphQL Client Service** (`shopify_graphql_client.py`)
   - ✅ Created GraphQL client with all product queries
   - ✅ Handles cursor-based pagination
   - ✅ Converts GraphQL responses to REST format for compatibility

2. **API Adapter Layer** (`shopify_api_adapter.py`)
   - ✅ Unified interface for both REST and GraphQL
   - ✅ Automatic fallback to REST if GraphQL fails
   - ✅ Feature flag support for gradual rollout

3. **Enhanced Sync Service** (`product_sync_service_v2.py`)
   - ✅ Drop-in replacement with GraphQL support
   - ✅ Backward compatibility maintained
   - ✅ Enhanced health checks and monitoring

4. **Test Suite** (`test_graphql_migration.py`)
   - ✅ Comprehensive comparison testing
   - ✅ Performance benchmarks
   - ✅ Migration readiness assessment

### Phase 2: Safe Migration (CURRENT)

#### Step 1: Test Your Store

```bash
# Test your store's compatibility
export TEST_STORE_URL="your-store.myshopify.com"
export TEST_ACCESS_TOKEN="shpat_xxxxx"
python test_graphql_migration.py --output migration_test_results.json
```

#### Step 2: Review Test Results

The test will check:
- Product count consistency between APIs
- Data format compatibility
- Performance comparison
- Single product fetching
- Overall migration readiness

#### Step 3: Enable GraphQL (Safe Mode)

Add to your `.env` file:
```bash
# Enable GraphQL API (with REST fallback)
USE_GRAPHQL_API=true
SHOPIFY_API_VERSION=2024-10
GRAPHQL_API_VERSION=2025-01
```

#### Step 4: Monitor and Validate

1. **Start with Low-Traffic Operations**:
   ```python
   # Test on a single store first
   from app.modules.whatsapp.product_sync_service_v2 import ProductSyncServiceV2
   
   # This will use GraphQL but fallback to REST on errors
   service = ProductSyncServiceV2(db)
   result = await service.health_check_product_count(store_url)
   ```

2. **Compare API Health**:
   ```python
   # Run comprehensive comparison
   result = await service.compare_apis_health_check(store_url)
   print(f"Ready for migration: {result['health_check']['ready_for_migration']}")
   ```

### Phase 3: Production Rollout

#### Option A: Environment Variable (Global)

```bash
# Enable for all stores
USE_GRAPHQL_API=true
```

#### Option B: Per-Store Migration (Recommended)

```python
# Migrate specific stores after validation
async def migrate_store(store_url: str):
    service = ProductSyncServiceV2(db)
    result = await service.migrate_store_to_graphql(store_url)
    if result["status"] == "success":
        print(f"✅ {store_url} ready for GraphQL")
    else:
        print(f"❌ {store_url} not ready: {result['message']}")
```

#### Option C: Gradual Rollout

```python
# Enable GraphQL for percentage of stores
import random

def should_use_graphql(store_url: str, rollout_percentage: int = 10) -> bool:
    # Deterministic rollout based on store URL
    hash_val = hash(store_url) % 100
    return hash_val < rollout_percentage

# In your sync service
use_graphql = should_use_graphql(store_url, rollout_percentage=25)  # 25% of stores
```

## Implementation Details

### Complete API Coverage ✅

**Now Implemented:**
- ✅ **Products & Variants** - Full GraphQL with REST fallback
- ✅ **Orders** - Complete order management with GraphQL
- ✅ **Customers** - Customer creation and fetching
- ✅ **Draft Orders** - Draft order creation and completion
- ✅ **Shop Information** - Store details and configuration
- ✅ **Webhooks** - Webhook management with GraphQL mutations

### Key Changes Made

1. **Complete API Coverage**:
   - All Shopify Admin APIs now have GraphQL implementations
   - Unified interface through `ShopifyAPIAdapter`
   - Automatic format conversion for backward compatibility

2. **Enhanced Services**:
   - `CompleteShopifyService` - Unified service for all APIs
   - `ProductSyncServiceV2` - Enhanced product sync with GraphQL
   - Comprehensive health checks across all APIs

3. **Backward Compatibility**:
   - All existing code continues to work unchanged
   - GraphQL responses are converted to REST format
   - Automatic fallback on GraphQL errors

4. **Enhanced Error Handling**:
   ```python
   # GraphQL errors fall back to REST automatically
   if "error" in graphql_result:
       print("[INFO] GraphQL failed, using REST fallback")
       return await self._fetch_products_rest()
   ```

5. **Performance Monitoring**:
   - Track API response times across all endpoints
   - Compare success rates between REST and GraphQL
   - Comprehensive performance benchmarking

### Configuration Options

```python
# app/core/config.py
class Settings(BaseSettings):
    USE_GRAPHQL_API: bool = False  # Main feature flag
    SHOPIFY_API_VERSION: str = "2024-10"  # REST version
    GRAPHQL_API_VERSION: str = "2025-01"  # GraphQL version
```

### Usage Examples

#### Basic Product Sync (No Changes Required)

```python
# Your existing code works unchanged
from app.modules.whatsapp.product_sync_service_v2 import ProductSyncServiceV2

service = ProductSyncServiceV2(db)
result = await service.initial_product_sync(store_url)
# Automatically uses GraphQL if USE_GRAPHQL_API=true
```

#### Override API Choice

```python
# Force GraphQL for specific operation
result = await service.initial_product_sync(store_url, use_graphql=True)

# Force REST for specific operation  
result = await service.initial_product_sync(store_url, use_graphql=False)
```

#### Health Monitoring

```python
# Compare both APIs
health = await service.compare_apis_health_check(store_url)
print(f"APIs consistent: {health['health_check']['apis_consistent']}")
print(f"Ready for migration: {health['health_check']['ready_for_migration']}")
```

### Complete API Usage Examples

#### Using the Unified Service

```python
from app.modules.whatsapp.complete_shopify_service import CompleteShopifyService

service = CompleteShopifyService(db)
store_url = "your-store.myshopify.com"

# Products API
products = await service.get_all_products(store_url, use_graphql=True)
print(f"Fetched {products['count']} products via {products['api_used']}")

# Orders API
orders = await service.get_orders(store_url, limit=10, use_graphql=True)
print(f"Fetched {orders['count']} orders via {orders['api_used']}")

# Customers API
customers = await service.get_customers(store_url, use_graphql=True)
print(f"Fetched {customers['count']} customers via {customers['api_used']}")

# Shop Info API
shop = await service.get_shop_info(store_url, use_graphql=True)
print(f"Shop: {shop['shop']['name']} via {shop['api_used']}")

# Draft Orders API
draft_order_data = {
    "line_items": [{"variant_id": 123, "quantity": 1}],
    "email": "customer@example.com"
}
draft = await service.create_draft_order(store_url, draft_order_data, use_graphql=True)
print(f"Draft order created: {draft['draft_order']['id']} via {draft['api_used']}")

# Webhooks API
webhooks = await service.get_webhooks(store_url, use_graphql=True)
print(f"Found {webhooks['count']} webhooks via {webhooks['api_used']}")
```

#### Using the API Adapter Directly

```python
from app.modules.whatsapp.shopify_api_adapter import ShopifyAPIAdapter

adapter = ShopifyAPIAdapter(store_url, access_token, use_graphql=True)

# Products
products = await adapter.fetch_all_products(limit=50)
single_product = await adapter.fetch_single_product("123456789")
count = await adapter.get_products_count()

# Orders
orders = await adapter.fetch_orders(limit=20, query="financial_status:paid")
single_order = await adapter.fetch_single_order("987654321")

# Customers
customers = await adapter.fetch_customers(limit=30)
new_customer = await adapter.create_customer({
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john@example.com"
})

# Draft Orders
draft_order = await adapter.create_draft_order({
    "line_items": [{"variant_id": 123, "quantity": 2}]
})
completed_order = await adapter.complete_draft_order("draft_order_id")

# Shop Info
shop_info = await adapter.get_shop_info()

# Webhooks
webhooks = await adapter.get_webhooks()
new_webhook = await adapter.create_webhook({
    "topic": "ORDERS_CREATE",
    "address": "https://yourapp.com/webhooks/orders"
})
```

#### GraphQL Client Direct Usage

```python
from app.modules.whatsapp.shopify_graphql_client import ShopifyGraphQLClient

client = ShopifyGraphQLClient(store_url, access_token, "2025-01")

# Products
products_result = await client.get_products(first=10)
product_by_id = await client.get_product_by_id("gid://shopify/Product/123")

# Orders
orders_result = await client.get_orders(first=5, query="tag:vip")
order_by_id = await client.get_order_by_id("gid://shopify/Order/456")

# Customers  
customers_result = await client.get_customers(first=20)
new_customer = await client.create_customer({
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane@example.com"
})

# Shop
shop_result = await client.get_shop_info()

# Convert to REST format for compatibility
rest_product = client.convert_graphql_to_rest_format(graphql_product)
rest_order = client.convert_order_graphql_to_rest(graphql_order)
rest_customer = client.convert_customer_graphql_to_rest(graphql_customer)
```

## Rollback Plan

If issues arise, you can quickly rollback:

1. **Environment Variable**:
   ```bash
   USE_GRAPHQL_API=false
   ```

2. **Code Level**:
   ```python
   # Force REST mode
   adapter.switch_to_rest()
   ```

3. **Automatic Fallback**:
   - GraphQL errors automatically fall back to REST
   - No manual intervention required

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Error Rates**:
   - GraphQL query failures
   - REST API fallback frequency
   - Overall sync success rate

2. **Performance**:
   - API response times
   - Product sync duration
   - Memory usage

3. **Data Consistency**:
   - Product count matching
   - Data format consistency
   - Webhook processing success

### Recommended Alerts

```python
# Set up monitoring
if graphql_error_rate > 5%:
    alert("High GraphQL error rate - consider rollback")

if rest_fallback_rate > 10%:
    alert("High REST fallback rate - investigate GraphQL issues")

if sync_duration_increase > 50%:
    alert("Sync performance degraded after GraphQL migration")
```

## Testing Checklist

Before enabling GraphQL in production:

- [ ] Run test script for all active stores
- [ ] Verify product counts match between APIs
- [ ] Test single product fetching
- [ ] Test product sync webhook handling
- [ ] Monitor error logs for GraphQL issues
- [ ] Validate data format consistency
- [ ] Test performance under load
- [ ] Verify fallback mechanisms work

## Troubleshooting

### Common Issues

1. **GraphQL Query Errors**:
   ```
   Solution: Check query syntax and field availability
   Fallback: Automatic REST API usage
   ```

2. **Rate Limiting**:
   ```
   GraphQL and REST have different rate limits
   Monitor 429 responses and adjust retry logic
   ```

3. **Data Format Differences**:
   ```
   GraphQL IDs are different format (gid://shopify/Product/123)
   Conversion handled automatically in adapter
   ```

4. **Pagination Changes**:
   ```
   GraphQL uses cursor-based pagination
   REST uses page-based pagination
   Handled transparently by adapter
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("shopify_graphql").setLevel(logging.DEBUG)
```

## Timeline & Milestones

### Week 1: Testing Phase
- [ ] Run test script on all stores
- [ ] Fix any identified issues
- [ ] Performance baseline measurements

### Week 2: Limited Rollout  
- [ ] Enable for 10% of stores
- [ ] Monitor error rates and performance
- [ ] Collect feedback and adjust

### Week 3: Expanded Rollout
- [ ] Enable for 50% of stores
- [ ] Continue monitoring
- [ ] Document any issues and solutions

### Week 4: Full Migration
- [ ] Enable for 100% of stores
- [ ] Remove REST fallback code (optional)
- [ ] Update documentation

## Support & Contact

For issues or questions during migration:
1. Check error logs first
2. Run diagnostic test script
3. Review this guide's troubleshooting section
4. Consider temporary rollback if critical issues arise

## Files Created/Modified

### New Files:
- `app/modules/whatsapp/shopify_graphql_client.py` - GraphQL client service
- `app/modules/whatsapp/shopify_api_adapter.py` - Unified API adapter
- `app/modules/whatsapp/product_sync_service_v2.py` - Enhanced sync service
- `test_graphql_migration.py` - Migration test suite
- `GRAPHQL_MIGRATION_GUIDE.md` - This guide

### Modified Files:
- `app/core/config.py` - Added GraphQL configuration options

### Files to Update (When Ready):
Replace usage of `ProductSyncService` with `ProductSyncServiceV2` in:
- Webhook handlers
- Scheduled tasks
- Admin endpoints
- Background jobs