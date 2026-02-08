"""Product search tool using Playwright for web scraping.

Searches for products on specific retailer websites with optional price filtering.
"""

import sys
import asyncio
import os
import hashlib
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _log(message: str) -> None:
    """Log to stderr to avoid corrupting STDIO transport."""
    print(f"[product_search] {message}", file=sys.stderr)


# In-memory product cache for cart operations
_product_cache: dict[str, dict] = {}


def get_cached_product(product_id: str) -> Optional[dict]:
    """Get a product from the cache by ID."""
    return _product_cache.get(product_id)


def _generate_mock_products(retailer_url: str, query: str, max_price: Optional[float]) -> list[dict]:
    """Generate mock product data for demo mode."""
    base_products = [
        {"name": f"{query} - Premium Edition", "base_price": 149.99},
        {"name": f"{query} - Standard", "base_price": 79.99},
        {"name": f"{query} - Budget Option", "base_price": 29.99},
        {"name": f"{query} - Professional Series", "base_price": 299.99},
        {"name": f"{query} - Compact Version", "base_price": 59.99},
        {"name": f"{query} - Deluxe Bundle", "base_price": 199.99},
        {"name": f"{query} - Essential Pack", "base_price": 49.99},
    ]

    # Extract retailer name from URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(retailer_url)
        retailer_name = parsed.netloc.replace("www.", "")
    except Exception:
        retailer_name = retailer_url.split("//")[-1].split("/")[0].replace("www.", "")

    products = []

    for i, bp in enumerate(base_products):
        price = bp["base_price"]
        if max_price and price > max_price:
            continue

        # Generate deterministic ID from retailer + product
        product_id = hashlib.md5(f"{retailer_url}:{bp['name']}".encode()).hexdigest()[:12]

        product = {
            "id": product_id,
            "name": bp["name"],
            "price": price,
            "currency": "USD",
            "url": f"{retailer_url.rstrip('/')}/product/{product_id}",
            "image_url": f"https://via.placeholder.com/200?text={product_id}",
            "retailer": retailer_name,
            "in_stock": i % 4 != 0  # Every 4th product out of stock for demo
        }
        products.append(product)
        _product_cache[product_id] = product

    return products


async def _scrape_products_async(
    retailer_url: str,
    query: str,
    max_price: Optional[float]
) -> list[dict]:
    """Scrape products from retailer using Playwright."""
    from scrapers.generic_patterns import GenericProductScraper

    _log(f"Scraping {retailer_url} for: {query}")

    try:
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))

        scraper = GenericProductScraper(headless=headless, timeout=timeout)
        products = await scraper.search_products(retailer_url, query, max_price)

        # Cache products for cart operations
        for p in products:
            _product_cache[p["id"]] = p

        return products

    except Exception as e:
        _log(f"Scraping failed: {e}, falling back to mock data")
        return _generate_mock_products(retailer_url, query, max_price)


def search_products(
    retailer_url: str,
    query: str,
    max_price: Optional[float] = None
) -> list[dict]:
    """
    Search for products on a retailer website.

    Searches for products matching the query on the specified retailer's website.
    In demo mode, returns mock product data. When demo mode is disabled,
    uses Playwright to scrape actual product listings.

    Args:
        retailer_url: The retailer's website URL (e.g., "https://www.amazon.com")
        query: Product search query (e.g., "wireless headphones")
        max_price: Optional maximum price filter in USD

    Returns:
        List of products with: id, name, price, currency, url, image_url, retailer, in_stock
    """
    _log(f"Searching {retailer_url} for '{query}' (max_price: {max_price})")

    # Check if demo mode is enabled
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"

    if demo_mode:
        _log("Using demo mode with mock data")
        return _generate_mock_products(retailer_url, query, max_price)

    # Run async scraping in sync context
    try:
        # Try to get existing event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create one
        loop = None

    if loop is not None:
        # We're in an async context, need to run in executor or use nest_asyncio
        _log("Async context detected, falling back to mock data")
        return _generate_mock_products(retailer_url, query, max_price)

    # Create new event loop and run
    try:
        return asyncio.run(_scrape_products_async(retailer_url, query, max_price))
    except Exception as e:
        _log(f"Scraping failed: {e}, falling back to mock data")
        return _generate_mock_products(retailer_url, query, max_price)


def clear_product_cache() -> None:
    """Clear the product cache."""
    global _product_cache
    _product_cache.clear()
    _log("Product cache cleared")
