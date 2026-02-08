#!/usr/bin/env python3
"""Shopping Agent MCP Server.

A Model Context Protocol server providing shopping assistance tools:
- Web search for finding retailers
- Product search on e-commerce sites
- Shopping cart management
- Mock checkout

Uses HTTP transport via dedalus-mcp-python on port 8000.
"""

import sys
import os
import logging
import asyncio
from typing import Optional

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()


def setup_logging() -> logging.Logger:
    """Configure logging to stderr.

    All logging goes to stderr to keep console output clean.
    """
    # Create stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Configure root logger
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        handlers=[handler]
    )

    return logging.getLogger("shopping-agent")


# Setup logging early
logger = setup_logging()


# Import dedalus-mcp
try:
    from dedalus_mcp import MCPServer, tool
except ImportError:
    logger.error("dedalus-mcp-python not installed. Install with: pip install dedalus-mcp-python")
    sys.exit(1)


# Import tool implementations
from tools.web_search import web_search as _web_search
from tools.product_search import search_products as _search_products
from tools.cart_management import (
    add_to_cart as _add_to_cart,
    view_cart as _view_cart,
    mock_checkout as _mock_checkout,
)
from tools.discover_product import discover_product as _discover_product


# Define tools using @tool decorator
@tool(description="Search the web for retailers and shopping sites. Returns a list of relevant URLs with titles and descriptions.")
def web_search(query: str, max_results: int = 10, region: str = None) -> list[dict]:
    """
    Search the web for retailers matching the query.

    Args:
        query: Search query string (e.g., "buy wireless headphones online")
        max_results: Maximum number of results to return (default: 10)
        region: Optional region code (e.g., "us-en", "uk-en")

    Returns:
        List of dicts with keys: title, url, description
    """
    logger.info(f"web_search called: query={query}, max_results={max_results}, region={region}")
    return _web_search(query=query, max_results=max_results, region=region)


@tool(description="Search for products on a specific retailer website. Returns product details including prices, availability, and URLs.")
def search_products(retailer_url: str, query: str, max_price: float = None) -> list[dict]:
    """
    Search for products on a retailer website.

    Args:
        retailer_url: The retailer's website URL (e.g., "https://www.amazon.com")
        query: Product search query (e.g., "wireless headphones")
        max_price: Optional maximum price filter in USD

    Returns:
        List of products with: id, name, price, currency, url, image_url, retailer, in_stock
    """
    logger.info(f"search_products called: retailer_url={retailer_url}, query={query}, max_price={max_price}")
    return _search_products(retailer_url=retailer_url, query=query, max_price=max_price)


@tool(description="Add a product to the shopping cart. Use the product_id from search_products results.")
def add_to_cart(product_id: str, quantity: int = 1) -> dict:
    """
    Add a product to the shopping cart.

    Args:
        product_id: The product ID from search_products results
        quantity: Number of items to add (default: 1)

    Returns:
        Dict with: success, message, cart summary (id, item_count, total)
    """
    logger.info(f"add_to_cart called: product_id={product_id}, quantity={quantity}")
    return _add_to_cart(product_id=product_id, quantity=quantity)


@tool(description="View the current shopping cart contents, including all items and totals.")
def view_cart() -> dict:
    """
    View the current shopping cart.

    Returns:
        Dict with: id, items (list), total, item_count, created_at, updated_at
    """
    logger.info("view_cart called")
    return _view_cart()


@tool(description="Perform a mock checkout. This simulates placing an order without real payment processing.")
def mock_checkout(cart_id: str) -> dict:
    """
    Perform a mock checkout operation.

    Args:
        cart_id: The cart ID to checkout

    Returns:
        Dict with: order_id, cart_id, status, total, items, message
    """
    logger.info(f"mock_checkout called: cart_id={cart_id}")
    return _mock_checkout(cart_id=cart_id)


@tool(description="Discover grocery products by name using the Kroger API. Returns product details including price, image, and size.")
def discover_product(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for grocery products by name.

    Args:
        query: Product search term (e.g., "organic milk", "frozen pizza")
        max_results: Maximum number of products to return (default: 5, max: 20)

    Returns:
        List of dicts with keys: product_id, name, price, sold_by, size, image_url
    """
    logger.info(f"discover_product called: query={query}, max_results={max_results}")
    return _discover_product(query=query, max_results=max_results)


def main() -> None:
    """Main entry point for the shopping agent MCP server."""
    logger.info("Starting Shopping Agent MCP Server...")

    # Create MCP server
    server = MCPServer("shopping-agent")

    # Register all tools
    server.collect(web_search)
    server.collect(search_products)
    server.collect(add_to_cart)
    server.collect(view_cart)
    server.collect(mock_checkout)
    server.collect(discover_product)

    logger.info("Tools registered: web_search, search_products, add_to_cart, view_cart, mock_checkout, discover_product")
    logger.info("Starting HTTP server on port 8000...")

    try:
        # Run server with HTTP transport on port 8000
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
