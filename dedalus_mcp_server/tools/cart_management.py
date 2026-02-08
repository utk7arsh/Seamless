"""Cart management tools with in-memory state.

Provides shopping cart functionality including add, view, and checkout operations.
"""

import sys
import uuid
from datetime import datetime
from typing import Optional

from tools.product_search import get_cached_product


def _log(message: str) -> None:
    """Log to stderr to avoid corrupting STDIO transport."""
    print(f"[cart] {message}", file=sys.stderr)


# In-memory cart storage (single cart for demo)
_cart: dict = {
    "id": str(uuid.uuid4()),
    "items": [],
    "total": 0.0,
    "item_count": 0,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}


def _recalculate_cart() -> None:
    """Recalculate cart totals."""
    global _cart
    total = sum(item["subtotal"] for item in _cart["items"])
    item_count = sum(item["quantity"] for item in _cart["items"])
    _cart["total"] = round(total, 2)
    _cart["item_count"] = item_count
    _cart["updated_at"] = datetime.utcnow().isoformat()


def add_to_cart(product_id: str, quantity: int = 1) -> dict:
    """
    Add a product to the shopping cart.

    Uses the product_id from search_products results to add items to the cart.
    If the product is already in the cart, the quantity is updated.

    Args:
        product_id: The product ID from search_products results
        quantity: Number of items to add (default: 1)

    Returns:
        Dict with: success, message, cart summary (id, item_count, total)
    """
    global _cart

    _log(f"Adding product {product_id} x{quantity} to cart")

    if quantity < 1:
        return {
            "success": False,
            "message": "Quantity must be at least 1",
            "cart": {
                "id": _cart["id"],
                "item_count": _cart["item_count"],
                "total": _cart["total"]
            }
        }

    # Look up product from cache
    product = get_cached_product(product_id)

    if not product:
        # Create placeholder if product not in cache (demo mode)
        _log(f"Product {product_id} not in cache, creating placeholder")
        product = {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 99.99,
            "currency": "USD"
        }

    # Check if product already in cart
    existing_item = None
    for item in _cart["items"]:
        if item["product_id"] == product_id:
            existing_item = item
            break

    if existing_item:
        existing_item["quantity"] += quantity
        existing_item["subtotal"] = round(
            existing_item["price"] * existing_item["quantity"], 2
        )
        _log(f"Updated quantity for {product_id}")
    else:
        new_item = {
            "product_id": product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "subtotal": round(product["price"] * quantity, 2)
        }
        _cart["items"].append(new_item)
        _log(f"Added new item {product_id}")

    _recalculate_cart()

    return {
        "success": True,
        "message": f"Added {quantity}x {product['name']} to cart",
        "cart": {
            "id": _cart["id"],
            "item_count": _cart["item_count"],
            "total": _cart["total"]
        }
    }


def view_cart() -> dict:
    """
    View the current shopping cart.

    Returns the complete cart state including all items and totals.

    Returns:
        Dict with: id, items (list), total, item_count, created_at, updated_at
    """
    _log("Viewing cart")
    return _cart.copy()


def mock_checkout(cart_id: str) -> dict:
    """
    Perform a mock checkout operation.

    Simulates placing an order without real payment processing.
    Clears the cart after successful checkout.

    Args:
        cart_id: The cart ID to checkout

    Returns:
        Dict with: order_id, cart_id, status, total, items, message
    """
    global _cart

    _log(f"Processing mock checkout for cart {cart_id}")

    if cart_id != _cart["id"]:
        return {
            "order_id": None,
            "cart_id": cart_id,
            "status": "error",
            "total": 0,
            "items": [],
            "message": f"Cart {cart_id} not found"
        }

    if not _cart["items"]:
        return {
            "order_id": None,
            "cart_id": cart_id,
            "status": "error",
            "total": 0,
            "items": [],
            "message": "Cart is empty"
        }

    # Generate order
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    result = {
        "order_id": order_id,
        "cart_id": cart_id,
        "status": "completed",
        "total": _cart["total"],
        "items": _cart["items"].copy(),
        "message": f"Mock order {order_id} placed successfully! Total: ${_cart['total']:.2f}"
    }

    # Clear cart after checkout
    _cart = {
        "id": str(uuid.uuid4()),
        "items": [],
        "total": 0.0,
        "item_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    _log(f"Order {order_id} created, cart cleared")

    return result


def clear_cart() -> dict:
    """
    Clear all items from the cart.

    Returns:
        Dict with: success, message
    """
    global _cart

    _log("Clearing cart")

    _cart = {
        "id": str(uuid.uuid4()),
        "items": [],
        "total": 0.0,
        "item_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    return {
        "success": True,
        "message": "Cart cleared",
        "cart": {
            "id": _cart["id"],
            "item_count": 0,
            "total": 0.0
        }
    }
