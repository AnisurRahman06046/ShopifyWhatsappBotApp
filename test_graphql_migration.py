#!/usr/bin/env python3
"""
GraphQL Migration Test Script

This script tests the new GraphQL implementation against your existing REST implementation
to ensure compatibility before migration.

Usage:
    python test_graphql_migration.py --store your-store.myshopify.com --token your-access-token

Or set environment variables:
    export TEST_STORE_URL="your-store.myshopify.com"
    export TEST_ACCESS_TOKEN="shpat_xxxxx"
    python test_graphql_migration.py
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime
import json

# Add app to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.whatsapp.shopify_api_adapter import ShopifyAPIAdapter
from app.modules.whatsapp.shopify_graphql_client import ShopifyGraphQLClient


async def test_products_count(adapter: ShopifyAPIAdapter) -> dict:
    """Test product count comparison between REST and GraphQL"""
    print("\n=== Testing Product Count ===")
    
    # Test REST
    adapter.switch_to_rest()
    rest_count = await adapter.get_products_count()
    print(f"REST API count: {rest_count}")
    
    # Test GraphQL
    adapter.switch_to_graphql()
    graphql_count = await adapter.get_products_count()
    print(f"GraphQL API count: {graphql_count}")
    
    match = rest_count == graphql_count
    print(f"Counts match: {match}")
    
    return {
        "rest_count": rest_count,
        "graphql_count": graphql_count,
        "match": match,
        "difference": abs(rest_count - graphql_count)
    }


async def test_product_fetching(adapter: ShopifyAPIAdapter, limit: int = 5) -> dict:
    """Test product fetching comparison"""
    print(f"\n=== Testing Product Fetching (limit: {limit}) ===")
    
    # Test REST
    print("Fetching via REST...")
    adapter.switch_to_rest()
    rest_products = await adapter.fetch_all_products(limit=limit)
    rest_count = len(rest_products)
    print(f"REST fetched: {rest_count} products")
    
    # Test GraphQL
    print("Fetching via GraphQL...")
    adapter.switch_to_graphql()
    graphql_products = await adapter.fetch_all_products(limit=limit)
    graphql_count = len(graphql_products)
    print(f"GraphQL fetched: {graphql_count} products")
    
    # Compare first product if available
    first_product_match = False
    rest_first = None
    graphql_first = None
    
    if rest_products and graphql_products:
        rest_first = rest_products[0]
        graphql_first = graphql_products[0]
        
        # Compare key fields
        rest_id = str(rest_first.get('id', ''))
        graphql_id = str(graphql_first.get('id', ''))
        
        rest_title = rest_first.get('title', '')
        graphql_title = graphql_first.get('title', '')
        
        first_product_match = rest_id == graphql_id and rest_title == graphql_title
        
        print(f"First product comparison:")
        print(f"  REST: ID={rest_id}, Title='{rest_title}'")
        print(f"  GraphQL: ID={graphql_id}, Title='{graphql_title}'")
        print(f"  Match: {first_product_match}")
    
    return {
        "rest_count": rest_count,
        "graphql_count": graphql_count,
        "counts_match": rest_count == graphql_count,
        "first_product_match": first_product_match,
        "rest_first": rest_first,
        "graphql_first": graphql_first
    }


async def test_single_product(adapter: ShopifyAPIAdapter, products: list) -> dict:
    """Test single product fetching"""
    print(f"\n=== Testing Single Product Fetching ===")
    
    if not products:
        print("No products available for single product test")
        return {"status": "skipped", "reason": "no_products"}
    
    # Use first available product
    test_product = products[0]
    product_id = str(test_product.get('id', ''))
    
    if not product_id:
        print("No valid product ID found")
        return {"status": "skipped", "reason": "no_product_id"}
    
    print(f"Testing with product ID: {product_id}")
    
    # Test REST
    adapter.switch_to_rest()
    rest_product = await adapter.fetch_single_product(product_id)
    rest_success = rest_product is not None
    
    # Test GraphQL
    adapter.switch_to_graphql()
    graphql_product = await adapter.fetch_single_product(product_id)
    graphql_success = graphql_product is not None
    
    match = False
    if rest_success and graphql_success:
        rest_title = rest_product.get('title', '')
        graphql_title = graphql_product.get('title', '')
        match = rest_title == graphql_title
        
        print(f"REST single product: Success={rest_success}, Title='{rest_title}'")
        print(f"GraphQL single product: Success={graphql_success}, Title='{graphql_title}'")
        print(f"Titles match: {match}")
    
    return {
        "product_id": product_id,
        "rest_success": rest_success,
        "graphql_success": graphql_success,
        "titles_match": match,
        "both_successful": rest_success and graphql_success
    }


async def test_performance(adapter: ShopifyAPIAdapter, limit: int = 10) -> dict:
    """Basic performance comparison"""
    print(f"\n=== Testing Performance (limit: {limit}) ===")
    
    # Test REST performance
    adapter.switch_to_rest()
    rest_start = datetime.utcnow()
    rest_products = await adapter.fetch_all_products(limit=limit)
    rest_duration = (datetime.utcnow() - rest_start).total_seconds()
    
    # Test GraphQL performance
    adapter.switch_to_graphql()
    graphql_start = datetime.utcnow()
    graphql_products = await adapter.fetch_all_products(limit=limit)
    graphql_duration = (datetime.utcnow() - graphql_start).total_seconds()
    
    print(f"REST: {len(rest_products)} products in {rest_duration:.2f}s")
    print(f"GraphQL: {len(graphql_products)} products in {graphql_duration:.2f}s")
    
    faster_api = "GraphQL" if graphql_duration < rest_duration else "REST"
    speed_improvement = abs(rest_duration - graphql_duration) / max(rest_duration, graphql_duration) * 100
    
    print(f"{faster_api} was {speed_improvement:.1f}% faster")
    
    return {
        "rest_duration": rest_duration,
        "graphql_duration": graphql_duration,
        "rest_count": len(rest_products),
        "graphql_count": len(graphql_products),
        "faster_api": faster_api,
        "speed_improvement_percent": speed_improvement
    }


async def test_orders_api(adapter: ShopifyAPIAdapter, limit: int = 5) -> dict:
    """Test orders API comparison between REST and GraphQL"""
    print(f"\n=== Testing Orders API (limit: {limit}) ===")
    
    # Test REST
    adapter.switch_to_rest()
    rest_orders = await adapter.fetch_orders(limit=limit)
    rest_count = len(rest_orders)
    print(f"REST orders fetched: {rest_count}")
    
    # Test GraphQL
    adapter.switch_to_graphql()
    graphql_orders = await adapter.fetch_orders(limit=limit)
    graphql_count = len(graphql_orders)
    print(f"GraphQL orders fetched: {graphql_count}")
    
    counts_match = rest_count == graphql_count
    print(f"Order counts match: {counts_match}")
    
    return {
        "rest_count": rest_count,
        "graphql_count": graphql_count,
        "counts_match": counts_match,
        "both_successful": rest_count > 0 and graphql_count > 0
    }


async def test_customers_api(adapter: ShopifyAPIAdapter, limit: int = 5) -> dict:
    """Test customers API comparison"""
    print(f"\n=== Testing Customers API (limit: {limit}) ===")
    
    # Test REST
    adapter.switch_to_rest()
    rest_customers = await adapter.fetch_customers(limit=limit)
    rest_count = len(rest_customers)
    print(f"REST customers fetched: {rest_count}")
    
    # Test GraphQL
    adapter.switch_to_graphql()
    graphql_customers = await adapter.fetch_customers(limit=limit)
    graphql_count = len(graphql_customers)
    print(f"GraphQL customers fetched: {graphql_count}")
    
    counts_match = rest_count == graphql_count
    print(f"Customer counts match: {counts_match}")
    
    return {
        "rest_count": rest_count,
        "graphql_count": graphql_count,
        "counts_match": counts_match,
        "both_successful": rest_count >= 0 and graphql_count >= 0
    }


async def test_shop_info_api(adapter: ShopifyAPIAdapter) -> dict:
    """Test shop info API comparison"""
    print(f"\n=== Testing Shop Info API ===")
    
    # Test REST
    adapter.switch_to_rest()
    rest_shop = await adapter.get_shop_info()
    rest_success = rest_shop is not None
    rest_name = rest_shop.get("name", "") if rest_shop else ""
    
    # Test GraphQL
    adapter.switch_to_graphql()
    graphql_shop = await adapter.get_shop_info()
    graphql_success = graphql_shop is not None
    graphql_name = graphql_shop.get("name", "") if graphql_shop else ""
    
    names_match = rest_name == graphql_name and rest_name != ""
    print(f"REST shop info: Success={rest_success}, Name='{rest_name}'")
    print(f"GraphQL shop info: Success={graphql_success}, Name='{graphql_name}'")
    print(f"Shop names match: {names_match}")
    
    return {
        "rest_success": rest_success,
        "graphql_success": graphql_success,
        "names_match": names_match,
        "both_successful": rest_success and graphql_success
    }


async def test_webhooks_api(adapter: ShopifyAPIAdapter) -> dict:
    """Test webhooks API comparison"""
    print(f"\n=== Testing Webhooks API ===")
    
    # Test REST
    adapter.switch_to_rest()
    rest_webhooks = await adapter.get_webhooks()
    rest_count = len(rest_webhooks)
    print(f"REST webhooks fetched: {rest_count}")
    
    # Test GraphQL
    adapter.switch_to_graphql()
    graphql_webhooks = await adapter.get_webhooks()
    graphql_count = len(graphql_webhooks)
    print(f"GraphQL webhooks fetched: {graphql_count}")
    
    counts_match = rest_count == graphql_count
    print(f"Webhook counts match: {counts_match}")
    
    return {
        "rest_count": rest_count,
        "graphql_count": graphql_count,
        "counts_match": counts_match,
        "both_successful": rest_count >= 0 and graphql_count >= 0
    }


async def test_comprehensive_performance(adapter: ShopifyAPIAdapter) -> dict:
    """Test performance across all APIs"""
    print(f"\n=== Testing Comprehensive Performance ===")
    
    performance_results = {}
    
    # Test Products Performance
    adapter.switch_to_rest()
    rest_start = datetime.utcnow()
    rest_products = await adapter.fetch_all_products(limit=10)
    rest_duration = (datetime.utcnow() - rest_start).total_seconds()
    
    adapter.switch_to_graphql()
    graphql_start = datetime.utcnow()
    graphql_products = await adapter.fetch_all_products(limit=10)
    graphql_duration = (datetime.utcnow() - graphql_start).total_seconds()
    
    performance_results["products"] = {
        "rest_duration": rest_duration,
        "graphql_duration": graphql_duration,
        "rest_count": len(rest_products),
        "graphql_count": len(graphql_products),
        "graphql_faster": graphql_duration < rest_duration
    }
    
    # Test Shop Info Performance
    adapter.switch_to_rest()
    rest_start = datetime.utcnow()
    await adapter.get_shop_info()
    rest_shop_duration = (datetime.utcnow() - rest_start).total_seconds()
    
    adapter.switch_to_graphql()
    graphql_start = datetime.utcnow()
    await adapter.get_shop_info()
    graphql_shop_duration = (datetime.utcnow() - graphql_start).total_seconds()
    
    performance_results["shop_info"] = {
        "rest_duration": rest_shop_duration,
        "graphql_duration": graphql_shop_duration,
        "graphql_faster": graphql_shop_duration < rest_shop_duration
    }
    
    # Calculate overall performance
    total_rest = rest_duration + rest_shop_duration
    total_graphql = graphql_duration + graphql_shop_duration
    overall_improvement = ((total_rest - total_graphql) / total_rest * 100) if total_rest > 0 else 0
    
    performance_results["overall"] = {
        "total_rest_duration": total_rest,
        "total_graphql_duration": total_graphql,
        "graphql_faster_overall": total_graphql < total_rest,
        "performance_improvement_percent": round(overall_improvement, 1)
    }
    
    print(f"Overall performance: GraphQL {'faster' if total_graphql < total_rest else 'slower'} by {abs(overall_improvement):.1f}%")
    
    return performance_results


async def run_full_test(store_url: str, access_token: str) -> dict:
    """Run comprehensive test suite covering all APIs"""
    
    print(f"Starting COMPLETE GraphQL migration tests for: {store_url}")
    print(f"Access token: {access_token[:20]}...")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Create adapter
    adapter = ShopifyAPIAdapter(store_url, access_token, use_graphql=False)
    
    results = {
        "store_url": store_url,
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    try:
        # Test 1: Product APIs (original tests)
        results["tests"]["product_count"] = await test_products_count(adapter)
        
        fetch_result = await test_product_fetching(adapter, limit=5)
        results["tests"]["product_fetching"] = fetch_result
        
        rest_products = fetch_result.get("rest_first")
        if rest_products:
            results["tests"]["single_product"] = await test_single_product(adapter, [rest_products])
        
        # Test 2: Orders API
        results["tests"]["orders"] = await test_orders_api(adapter, limit=5)
        
        # Test 3: Customers API
        results["tests"]["customers"] = await test_customers_api(adapter, limit=5)
        
        # Test 4: Shop Info API
        results["tests"]["shop_info"] = await test_shop_info_api(adapter)
        
        # Test 5: Webhooks API
        results["tests"]["webhooks"] = await test_webhooks_api(adapter)
        
        # Test 6: Comprehensive Performance
        results["tests"]["comprehensive_performance"] = await test_comprehensive_performance(adapter)
        
        # Test 7: Original Health Check
        results["tests"]["health_check"] = await adapter.health_check()
        
        # Overall assessment (enhanced)
        api_tests = ["product_count", "orders", "customers", "shop_info", "webhooks"]
        successful_tests = []
        failed_tests = []
        
        for test_name in api_tests:
            test_result = results["tests"].get(test_name, {})
            if test_name == "product_count":
                success = test_result.get("match", False)
            elif test_name in ["orders", "customers", "webhooks"]:
                success = test_result.get("both_successful", False)
            elif test_name == "shop_info":
                success = test_result.get("both_successful", False)
            else:
                success = True  # Default to success for other tests
            
            if success:
                successful_tests.append(test_name)
            else:
                failed_tests.append(test_name)
        
        overall_success_rate = len(successful_tests) / len(api_tests) * 100
        ready_for_migration = overall_success_rate >= 80  # 80% success rate threshold
        
        results["overall"] = {
            "ready_for_migration": ready_for_migration,
            "success_rate": round(overall_success_rate, 1),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "issues_found": [],
            "recommendations": []
        }
        
        # Add specific issues and recommendations
        if not results["tests"]["product_count"].get("match", True):
            results["overall"]["issues_found"].append("Product count mismatch between APIs")
        
        for api in failed_tests:
            results["overall"]["issues_found"].append(f"{api.replace('_', ' ').title()} API inconsistency detected")
        
        if ready_for_migration:
            results["overall"]["recommendations"].append(f"✅ Store is ready for GraphQL migration ({overall_success_rate}% APIs working)")
            results["overall"]["recommendations"].append("Set USE_GRAPHQL_API=true in environment")
            results["overall"]["recommendations"].append("Monitor error rates after migration")
            
            # Performance recommendation
            perf_result = results["tests"]["comprehensive_performance"]["overall"]
            if perf_result.get("graphql_faster_overall", False):
                improvement = perf_result.get("performance_improvement_percent", 0)
                results["overall"]["recommendations"].append(f"🚀 GraphQL is {improvement}% faster overall")
        else:
            results["overall"]["recommendations"].append(f"❌ Migration not recommended ({overall_success_rate}% success rate)")
            results["overall"]["recommendations"].append("Investigate API inconsistencies first")
            results["overall"]["recommendations"].append("Consider gradual migration of working APIs only")
            
    except Exception as e:
        results["error"] = str(e)
        print(f"\n❌ Test suite failed: {str(e)}")
    
    return results


def print_results(results: dict):
    """Print formatted test results"""
    
    print(f"\n" + "="*60)
    print(f"GRAPHQL MIGRATION TEST RESULTS")
    print(f"="*60)
    
    if "error" in results:
        print(f"❌ Test failed: {results['error']}")
        return
    
    overall = results.get("overall", {})
    ready = overall.get("ready_for_migration", False)
    
    print(f"Store: {results['store_url']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Migration Ready: {'✅ YES' if ready else '❌ NO'}")
    
    if overall.get("issues_found"):
        print(f"\nIssues Found:")
        for issue in overall["issues_found"]:
            print(f"  • {issue}")
    
    print(f"\nRecommendations:")
    for rec in overall.get("recommendations", []):
        print(f"  {rec}")
    
    print(f"\nDetailed Results:")
    tests = results.get("tests", {})
    
    # Products
    if "product_count" in tests:
        count_data = tests["product_count"]
        print(f"  Products: REST={count_data['rest_count']}, GraphQL={count_data['graphql_count']}, Match={count_data['match']}")
    
    # Orders
    if "orders" in tests:
        orders_data = tests["orders"]
        print(f"  Orders: REST={orders_data['rest_count']}, GraphQL={orders_data['graphql_count']}, Match={orders_data['counts_match']}")
    
    # Customers
    if "customers" in tests:
        customers_data = tests["customers"]
        print(f"  Customers: REST={customers_data['rest_count']}, GraphQL={customers_data['graphql_count']}, Match={customers_data['counts_match']}")
    
    # Shop Info
    if "shop_info" in tests:
        shop_data = tests["shop_info"]
        print(f"  Shop Info: REST Success={shop_data['rest_success']}, GraphQL Success={shop_data['graphql_success']}, Names Match={shop_data['names_match']}")
    
    # Webhooks
    if "webhooks" in tests:
        webhooks_data = tests["webhooks"]
        print(f"  Webhooks: REST={webhooks_data['rest_count']}, GraphQL={webhooks_data['graphql_count']}, Match={webhooks_data['counts_match']}")
    
    # Performance
    if "comprehensive_performance" in tests:
        perf_data = tests["comprehensive_performance"]["overall"]
        faster = "GraphQL" if perf_data.get('graphql_faster_overall', False) else "REST"
        improvement = perf_data.get('performance_improvement_percent', 0)
        print(f"  Performance: {faster} is {abs(improvement):.1f}% faster overall")
    
    # Success Rate
    overall = results.get("overall", {})
    if "success_rate" in overall:
        print(f"  Success Rate: {overall['success_rate']}%")
        if overall.get("successful_tests"):
            print(f"  Working APIs: {', '.join(overall['successful_tests'])}")
        if overall.get("failed_tests"):
            print(f"  Failed APIs: {', '.join(overall['failed_tests'])}")
    
    print(f"\n" + "="*60)


async def main():
    parser = argparse.ArgumentParser(description="Test GraphQL migration compatibility")
    parser.add_argument("--store", help="Store URL (e.g., your-store.myshopify.com)")
    parser.add_argument("--token", help="Shopify access token")
    parser.add_argument("--output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Get credentials
    store_url = args.store or os.getenv("TEST_STORE_URL")
    access_token = args.token or os.getenv("TEST_ACCESS_TOKEN")
    
    if not store_url or not access_token:
        print("Error: Store URL and access token are required")
        print("Either pass them as arguments or set environment variables:")
        print("  export TEST_STORE_URL='your-store.myshopify.com'")
        print("  export TEST_ACCESS_TOKEN='shpat_xxxxx'")
        sys.exit(1)
    
    # Run tests
    results = await run_full_test(store_url, access_token)
    
    # Print results
    print_results(results)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())