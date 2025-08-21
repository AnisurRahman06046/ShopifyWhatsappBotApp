#!/usr/bin/env python3
"""Test the billing system endpoints"""

import requests
import json

# Test billing plans endpoint
def test_billing_plans():
    try:
        response = requests.get("http://localhost:8000/billing/plans")
        if response.status_code == 200:
            plans = response.json()["plans"]
            print("✅ Billing Plans Available:")
            for plan in plans:
                print(f"  📦 {plan['name']}: ${plan['price']}/month")
                print(f"     - {plan['messages_limit']:,} messages")
                print(f"     - {plan['trial_days']} day trial")
                print(f"     - Features: {len(plan['features'])} items")
                print()
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

# Test plan selection page
def test_plan_selection():
    try:
        response = requests.get("http://localhost:8000/billing/select-plan?shop=test-store.myshopify.com")
        if response.status_code == 200:
            print("✅ Plan Selection Page: Available")
            print(f"   📄 Page size: {len(response.text)} characters")
            if "Choose Your Plan" in response.text:
                print("   ✅ Contains plan selection UI")
            if "Free Plan" in response.text:
                print("   ✅ Free plan option available")
            if "trial" in response.text.lower():
                print("   ✅ Free trial mentioned")
        else:
            print(f"❌ Plan selection error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Billing System...\n")
    test_billing_plans()
    test_plan_selection()