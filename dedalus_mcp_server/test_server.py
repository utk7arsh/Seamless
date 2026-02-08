#!/usr/bin/env python3
"""Test script for Shopping Agent MCP Server.

Tests the MCP tools directly without running the full server.
Run with: python test_server.py
"""

import sys
import os

# Ensure demo mode for tests
os.environ["DEMO_MODE"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce noise during tests

from tools import (
    web_search,
    search_products,
    add_to_cart,
    view_cart,
    mock_checkout,
    discover_product,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_json(data: dict, indent: int = 2) -> None:
    """Pretty print JSON data."""
    import json
    print(json.dumps(data, indent=indent))


def test_web_search() -> bool:
    """Test the web_search tool."""
    print_section("Testing web_search")

    try:
        results = web_search("buy wireless headphones online", max_results=5)
        print(f"Found {len(results)} results:")
        for r in results[:3]:
            print(f"  - {r.get('title', 'N/A')[:50]}")
            print(f"    URL: {r.get('url', 'N/A')[:60]}")
        print(f"\n✓ web_search passed")
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_search_products() -> list[dict]:
    """Test the search_products tool."""
    print_section("Testing search_products")

    try:
        products = search_products(
            retailer_url="https://example-shop.com",
            query="wireless headphones",
            max_price=200.0
        )
        print(f"Found {len(products)} products:")
        for p in products[:5]:
            stock_status = "✓ In Stock" if p.get("in_stock", True) else "✗ Out of Stock"
            print(f"  - {p['name']}")
            print(f"    ID: {p['id']}, Price: ${p['price']:.2f}, {stock_status}")
        print(f"\n✓ search_products passed")
        return products
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return []


def test_cart_operations(products: list[dict]) -> str:
    """Test cart management tools."""
    print_section("Testing Cart Operations")

    try:
        # View empty cart
        print("1. Viewing empty cart:")
        cart = view_cart()
        print(f"   Cart ID: {cart['id']}")
        print(f"   Items: {cart['item_count']}, Total: ${cart['total']:.2f}")

        # Add products
        if products:
            print("\n2. Adding products to cart:")
            for p in products[:2]:
                result = add_to_cart(p["id"], quantity=1)
                print(f"   {result['message']}")

            # Add same product again (should update quantity)
            if products:
                result = add_to_cart(products[0]["id"], quantity=2)
                print(f"   {result['message']}")

        # View cart with items
        print("\n3. Viewing cart with items:")
        cart = view_cart()
        print(f"   Cart ID: {cart['id']}")
        print(f"   Items: {cart['item_count']}, Total: ${cart['total']:.2f}")
        for item in cart["items"]:
            print(f"   - {item['name']} x{item['quantity']} = ${item['subtotal']:.2f}")

        print(f"\n✓ cart operations passed")
        return cart["id"]

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return ""


def test_checkout(cart_id: str) -> bool:
    """Test the mock_checkout tool."""
    print_section("Testing mock_checkout")

    try:
        # Test with wrong cart ID
        print("1. Testing with invalid cart ID:")
        result = mock_checkout("invalid-cart-id")
        print(f"   Status: {result['status']}, Message: {result['message']}")

        # Test with correct cart ID
        print("\n2. Testing with valid cart ID:")
        result = mock_checkout(cart_id)
        print(f"   Order ID: {result['order_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Total: ${result['total']:.2f}")
        print(f"   Message: {result['message']}")

        # Verify cart is cleared
        print("\n3. Verifying cart is cleared:")
        cart = view_cart()
        print(f"   New Cart ID: {cart['id']}")
        print(f"   Items: {cart['item_count']} (should be 0)")

        if result["status"] == "completed":
            print(f"\n✓ mock_checkout passed")
            return True
        else:
            print(f"\n✗ mock_checkout failed - status was not 'completed'")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_price_filter() -> bool:
    """Test price filtering in product search."""
    print_section("Testing Price Filter")

    try:
        # Search with no price limit
        all_products = search_products(
            retailer_url="https://example-shop.com",
            query="laptop",
            max_price=None
        )
        print(f"Products without price filter: {len(all_products)}")

        # Search with price limit
        filtered_products = search_products(
            retailer_url="https://example-shop.com",
            query="laptop",
            max_price=100.0
        )
        print(f"Products with max_price=100: {len(filtered_products)}")

        # Verify all filtered products are under max price
        all_under_limit = all(p["price"] <= 100.0 for p in filtered_products)
        if all_under_limit:
            print("✓ All filtered products are under $100")
            return True
        else:
            print("✗ Some products exceed the price limit")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def test_discover_product() -> bool:
    """Test the discover_product tool."""
    print_section("Testing discover_product")

    try:
        results = discover_product("organic milk", max_results=3)
        print(f"Found {len(results)} products:")
        for p in results:
            print(f"  - {p['name']}")
            print(f"    Price: ${p['price']:.2f}, Size: {p.get('size', 'N/A')}")
            print(f"    Image: {p.get('image_url', 'N/A')[:60]}")

        assert len(results) > 0, "Should return at least one result"
        assert len(results) <= 3, "Should respect max_results"
        for p in results:
            assert "product_id" in p, "Missing product_id"
            assert "name" in p, "Missing name"
            assert "price" in p, "Missing price"
            assert "image_url" in p, "Missing image_url"

        print(f"\n✓ discover_product passed")
        return True
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main() -> int:
    """Run all tests."""
    print("\n" + "="*60)
    print("  Shopping Agent MCP Server - Test Suite")
    print("="*60)

    # Track test results
    results = {}

    # Test web search
    results["web_search"] = test_web_search()

    # Test product search
    products = test_search_products()
    results["search_products"] = len(products) > 0

    # Test price filter
    results["price_filter"] = test_price_filter()

    # Test cart operations
    cart_id = test_cart_operations(products)
    results["cart_operations"] = bool(cart_id)

    # Test checkout
    results["checkout"] = test_checkout(cart_id)

    # Test discover product
    results["discover_product"] = test_discover_product()

    # Print summary
    print_section("Test Summary")
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print(f"\n  🎉 ALL TESTS PASSED")
    else:
        print(f"\n  ⚠️  SOME TESTS FAILED")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
