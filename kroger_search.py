"""Kroger product discovery for Seamless ads."""

import os
from abc import ABC, abstractmethod
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from .schemas import UserProfile, AdAttributes, ProductResult


class ToolClient(ABC):
    """Abstract interface for grocery store API tools."""

    @abstractmethod
    def search_products(self, query: str, filters: dict) -> dict:
        pass

    @abstractmethod
    def get_product(self, product_id: str) -> dict: 
        pass

    @abstractmethod
    def add_to_cart(self, items: list[dict]) -> dict:
        pass

    @abstractmethod
    def get_cart(self, cart_id: str) -> dict:
        pass

    @abstractmethod
    def get_delivery_options(self, zip: Optional[str] = None) -> dict:
        pass


def _image_url_from_kroger_product(product: dict) -> Optional[str]:
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


class MockKrogerToolClient(ToolClient):
    """Mock Kroger client with deterministic query-shaped results."""

    def search_products(self, query: str, filters: dict) -> dict:
        max_price = float(filters.get("max_price", 100))
        base_price = min(max_price, 6.49)
        results = []
        for i in range(1, 6):
            results.append(
                {
                    "id": f"kroger_generic_{query[:8]}_{i}",
                    "name": f"{query.title()} Variant {i}",
                    "price": round(base_price + (i - 1) * 0.6, 2),
                    "unit": "item",
                    "size": "1 unit",
                    "in_stock": True,
                    "image_url": "https://images.kroger.com/product/generic-item.jpg",
                }
            )
        return {"results": results[:3], "total": len(results), "query": query, "provider": "kroger_mock"}

    def get_product(self, product_id: str) -> dict:
        return {
            "id": product_id,
            "name": f"Product {product_id}",
            "price": 5.99,
            "available": True,
            "unit": "item",
            "size": "1 unit",
            "image_url": "https://images.kroger.com/product/generic-item.jpg",
        }

    def add_to_cart(self, items: list[dict]) -> dict:
        return {"items_added": len(items), "success": True, "provider": "kroger_mock"}

    def get_cart(self, cart_id: str) -> dict:
        return {"cart_id": cart_id, "items": [], "subtotal": 0.0, "provider": "kroger_mock"}

    def get_delivery_options(self, zip: Optional[str] = None) -> dict:
        return {"zip": zip or "00000", "windows": [], "provider": "kroger_mock"}


class KrogerAPIClient(ToolClient):
    """Real Kroger API client using OAuth2."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        location_id: Optional[str] = None,
    ):
        self.client_id = (client_id or os.environ.get("KROGER_CLIENT_ID", "")).strip()
        self.client_secret = (client_secret or os.environ.get("KROGER_CLIENT_SECRET", "")).strip()
        self.access_token = (access_token or os.environ.get("KROGER_ACCESS_TOKEN", "")).strip()
        self.location_id = (location_id or os.environ.get("KROGER_LOCATION_ID", "")).strip()
        env = (os.environ.get("KROGER_ENV", "production") or "production").strip().lower()
        self.base_url = "https://api-ce.kroger.com/v1" if env == "ce" else "https://api.kroger.com/v1"

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Kroger API credentials required.")
        if not self.access_token:
            self.access_token = self._get_access_token()
        self._resolved_location_id: Optional[str] = None

    def _get_access_token(self) -> str:
        if requests is None:
            raise RuntimeError("Install requests to use KrogerAPIClient: pip install requests")
        token_path = "/v1/connect/oauth2/token"
        auth_url = self.base_url.replace("/v1", "") + token_path
        response = requests.post(
            auth_url,
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _headers(self) -> dict:
        return {"Accept": "application/json", "Authorization": f"Bearer {self.access_token}"}

    def _resolve_location_id(self, zip_code: Optional[str]) -> Optional[str]:
        if not zip_code:
            return None
        if self._resolved_location_id:
            return self._resolved_location_id
        if requests is None:
            return None
        try:
            url = f"{self.base_url}/locations"
            params = {"filter.zipCode.near": zip_code, "filter.limit": 1}
            response = requests.get(url, params=params, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            locations = data.get("data", [])
            if locations:
                self._resolved_location_id = locations[0].get("locationId")
            return self._resolved_location_id
        except Exception:
            return None

    def search_products(self, query: str, filters: dict) -> dict:
        if requests is None:
            raise RuntimeError("Install requests: pip install requests")
        term = (query or "").strip()
        if len(term) < 3:
            term = f"{query} grocery"[:50] if query else "groceries"
        params = {"filter.term": term, "filter.limit": int(filters.get("limit", 10))}
        location_id = self.location_id or self._resolve_location_id(filters.get("zip"))
        if location_id:
            params["filter.locationId"] = location_id
        url = f"{self.base_url}/products"
        response = requests.get(url, params=params, headers=self._headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        results = []
        for product in data.get("data", []):
            price = 0.0
            unit = "each"
            size = ""
            if product.get("items"):
                item = product["items"][0]
                if item.get("price"):
                    price = item["price"].get("regular", 0.0)
                unit = item.get("soldBy", "each")
                size = item.get("size", "") or ""
            image_url = _image_url_from_kroger_product(product)
            results.append(
                {
                    "id": product.get("productId", ""),
                    "name": product.get("description", ""),
                    "price": price,
                    "unit": unit,
                    "size": size or "each",
                    "in_stock": True,
                    "image_url": image_url,
                }
            )
        return {"results": results, "total": len(results), "query": query, "provider": "kroger_api"}

    def get_product(self, product_id: str) -> dict:
        if requests is None:
            raise RuntimeError("Install requests: pip install requests")
        url = f"{self.base_url}/products/{product_id}"
        params = {}
        if self.location_id:
            params["filter.locationId"] = self.location_id
        response = requests.get(url, params=params, headers=self._headers(), timeout=30)
        response.raise_for_status()
        data = response.json()
        product = data.get("data", {})
        price = 0.0
        unit = "each"
        size = ""
        if product.get("items"):
            item = product["items"][0]
            if item.get("price"):
                price = item["price"].get("regular", 0.0)
            unit = item.get("soldBy", "each")
            size = item.get("size", "") or ""
        return {
            "id": product.get("productId", ""),
            "name": product.get("description", ""),
            "price": price,
            "available": True,
            "unit": unit,
            "size": size or "each",
        }

    def add_to_cart(self, items: list[dict]) -> dict:
        return {
            "cart_id": None,
            "items_added": len(items),
            "success": True,
            "provider": "kroger_api",
            "message": "Kroger doesn't support cart API. Use search links to add items manually.",
        }

    def get_cart(self, cart_id: Optional[str]) -> dict:
        return {"cart_id": cart_id, "message": "Kroger doesn't support cart retrieval via API.", "provider": "kroger_api"}

    def get_delivery_options(self, zip: Optional[str] = None) -> dict:
        return {"zip": zip or "", "windows": [], "provider": "kroger_api"}


def get_kroger_client() -> ToolClient:
    cid = (os.environ.get("KROGER_CLIENT_ID") or "").strip()
    secret = (os.environ.get("KROGER_CLIENT_SECRET") or "").strip()
    if not cid or not secret:
        raise RuntimeError("Kroger API credentials required. Set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET.")
    return KrogerAPIClient()


def _price_filter(price_sensitivity: str) -> float:
    if price_sensitivity == "low":
        return 8.0
    if price_sensitivity == "high":
        return 20.0
    return 12.0


def _build_query(product_key: str, user: UserProfile) -> str:
    prefs = {p.lower() for p in user.dietary_preferences}
    if product_key == "pizza":
        if "vegetarian" in prefs or "no_beef" in prefs or "no_pork" in prefs:
            return "vegetarian frozen pizza"
        return "frozen pizza"
    if product_key == "coke":
        if user.brand_affinities.get("Coca-Cola", 0.0) >= 0.6:
            return "Coca-Cola"
        return "cola soda"
    if product_key == "laptop":
        return "laptop computer"
    return product_key


def _rank_results(results: list[dict], price_sensitivity: str, brand_bias: list[str]) -> list[dict]:
    def score(result: dict) -> tuple:
        name = (result.get("name") or "").lower()
        brand_hit = 1 if any(brand.lower() in name for brand in brand_bias) else 0
        price = float(result.get("price", 999.0))
        if price_sensitivity == "high":
            return (not result.get("in_stock", True), -brand_hit, -price)
        return (not result.get("in_stock", True), -brand_hit, price)

    return sorted(results, key=score)


def find_kroger_products(
    product_key: str,
    user_profile: UserProfile,
    targeting_context: AdAttributes,
    tool_client: Optional[ToolClient] = None,
) -> list[ProductResult]:
    client = tool_client or get_kroger_client()
    query = _build_query(product_key, user_profile)
    max_price = _price_filter(targeting_context.price_sensitivity)
    filters = {"max_price": max_price, "limit": 6, "zip": user_profile.location_zip}
    search = client.search_products(query, filters)
    results = search.get("results", [])
    if not results:
        relaxed_filters = {"max_price": max_price * 2, "limit": 10, "zip": user_profile.location_zip}
        fallback_queries = [query, product_key, "pizza", "Coca-Cola", "cola soda", "laptop computer"]
        for fallback in fallback_queries:
            search = client.search_products(fallback, relaxed_filters)
            results = search.get("results", [])
            if results:
                query = fallback
                break
    brand_bias = [k for k, v in user_profile.brand_affinities.items() if v >= 0.5]
    ranked = _rank_results(results, targeting_context.price_sensitivity, brand_bias)

    results: list[ProductResult] = []
    for product in ranked[:3]:
        image_url = product.get("image_url") or "https://images.kroger.com/product/generic-item.jpg"
        results.append(
            ProductResult(
                product_id=product.get("id", ""),
                name=product.get("name", ""),
                price=float(product.get("price", 0.0)),
                size=product.get("size", "each"),
                unit=product.get("unit", "each"),
                in_stock=bool(product.get("in_stock", True)),
                image_url=image_url,
                kroger_search_query=query,
            )
        )
    return results
