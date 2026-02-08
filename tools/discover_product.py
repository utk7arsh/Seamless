"""Discover product tool using Kroger API.

Searches for grocery products by name and returns product details
including price, image URL, size, and availability.
"""

import sys
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _log(message: str) -> None:
    """Log to stderr to avoid corrupting STDIO transport."""
    print(f"[discover_product] {message}", file=sys.stderr)


def _image_url_from_kroger_product(product: dict) -> Optional[str]:
    """Extract the best image URL from a Kroger product response.

    Prefers medium-size images, falls back to any available URL.
    """
    images = product.get("images") or []
    for img in images:
        sizes = img.get("sizes") or []
        url = None
        for s in sizes:
            if s.get("url"):
                if (s.get("size") or "").lower() == "medium":
                    return s["url"]
                if url is None:
                    url = s["url"]
        if url:
            return url
    return None


class _KrogerClient:
    """Lightweight Kroger API client for product discovery.

    Handles OAuth2 client_credentials authentication and product search.
    """

    def __init__(self):
        self.client_id = os.environ.get("KROGER_CLIENT_ID", "").strip()
        self.client_secret = os.environ.get("KROGER_CLIENT_SECRET", "").strip()
        self.location_id = os.environ.get("KROGER_LOCATION_ID", "").strip() or "01400513"
        env = os.environ.get("KROGER_ENV", "production").strip().lower()
        self.base_url = (
            "https://api-ce.kroger.com/v1" if env == "ce"
            else "https://api.kroger.com/v1"
        )
        self.access_token: Optional[str] = None

    def _ensure_token(self) -> None:
        """Obtain an OAuth2 access token if we don't have one."""
        if self.access_token:
            return
        import requests

        token_url = self.base_url.replace("/v1", "") + "/v1/connect/oauth2/token"
        _log(f"Requesting OAuth2 token from {token_url}")
        response = requests.post(
            token_url,
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        self.access_token = response.json()["access_token"]
        _log("OAuth2 token obtained successfully")

    def _headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Search Kroger products and return normalized results."""
        import requests

        self._ensure_token()

        term = (query or "").strip()
        if len(term) < 3:
            term = f"{query} grocery"[:50] if query else "groceries"

        params = {
            "filter.term": term,
            "filter.limit": limit,
        }
        if self.location_id:
            params["filter.locationId"] = self.location_id

        url = f"{self.base_url}/products"
        _log(f"Searching Kroger API: term={term} limit={limit}")
        response = requests.get(
            url, params=params, headers=self._headers(), timeout=30
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for product in data.get("data", []):
            price = 0.0
            sold_by = "each"
            size = ""
            if product.get("items"):
                item = product["items"][0]
                if item.get("price"):
                    price = item["price"].get("regular", 0.0)
                sold_by = item.get("soldBy", "each")
                size = item.get("size", "") or ""
            image_url = _image_url_from_kroger_product(product)
            results.append({
                "product_id": product.get("productId", ""),
                "name": product.get("description", ""),
                "price": price,
                "sold_by": sold_by,
                "size": size or "N/A",
                "image_url": image_url,
            })

        _log(f"Kroger API returned {len(results)} products")
        return results


def _mock_results(query: str, max_results: int) -> list[dict]:
    """Generate mock product results when Kroger credentials are unavailable."""
    mock_products = []
    variants = [
        ("Organic", 5.99),
        ("Store Brand", 3.49),
        ("Premium", 8.99),
        ("Family Size", 7.49),
        ("Single Serve", 2.99),
    ]
    for i, (suffix, price) in enumerate(variants[:max_results], start=1):
        mock_products.append({
            "product_id": f"mock_{query.replace(' ', '_')[:12]}_{i}",
            "name": f"{query.title()} - {suffix}",
            "price": price,
            "sold_by": "each",
            "size": "1 unit",
            "image_url": "https://images.kroger.com/product/generic-item.jpg",
        })
    return mock_products


def discover_product(query: str, max_results: int = 5) -> list[dict]:
    """
    Search for grocery products by name using the Kroger API.

    Returns product details including name, price, size, and image URL.
    Falls back to mock data when Kroger API credentials are not configured.

    Args:
        query: Product search term (e.g., "organic milk", "frozen pizza")
        max_results: Maximum number of products to return (default: 5, max: 20)

    Returns:
        List of dicts with keys: product_id, name, price, sold_by, size, image_url
    """
    _log(f"Discovering products for: {query}")

    max_results = min(max(1, max_results), 20)

    client_id = os.environ.get("KROGER_CLIENT_ID", "").strip()
    client_secret = os.environ.get("KROGER_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        _log("Kroger credentials not found, using mock data")
        return _mock_results(query, max_results)

    try:
        client = _KrogerClient()
        return client.search(query, limit=max_results)
    except Exception as e:
        _log(f"Kroger API error: {e}, falling back to mock data")
        return _mock_results(query, max_results)
