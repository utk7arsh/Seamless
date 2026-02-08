"""Shopping Agent Tools Package.

Exports all MCP tools for the shopping agent server.
"""

from tools.web_search import web_search
from tools.product_search import search_products
from tools.cart_management import add_to_cart, view_cart, mock_checkout
from tools.discover_product import discover_product

__all__ = [
    "web_search",
    "search_products",
    "add_to_cart",
    "view_cart",
    "mock_checkout",
    "discover_product",
]
