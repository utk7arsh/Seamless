"""Generic e-commerce product scraper using Playwright.

Provides pattern-based scraping for common e-commerce site structures.
"""

import sys
import hashlib
from typing import Optional


def _log(message: str) -> None:
    """Log to stderr to avoid corrupting STDIO transport."""
    print(f"[scraper] {message}", file=sys.stderr)


class GenericProductScraper:
    """
    Generic scraper that identifies common e-commerce patterns.

    Looks for common selectors used by major e-commerce platforms:
    - Product cards/tiles
    - Price elements
    - Product titles
    - Add to cart buttons
    - Stock indicators
    """

    # Common selectors for product elements
    PRODUCT_SELECTORS = [
        "[data-testid='product-card']",
        "[data-component='product-card']",
        ".product-card",
        ".product-tile",
        ".product-item",
        "[itemtype*='Product']",
        ".s-result-item",  # Amazon
        ".product-grid-item",
        "[data-asin]",  # Amazon
        ".plp-product-card",
    ]

    TITLE_SELECTORS = [
        "[data-testid='product-title']",
        ".product-title",
        ".product-name",
        "h2.product-title",
        "h3.product-name",
        "[itemprop='name']",
        ".a-text-normal",  # Amazon
        "h2 a span",
    ]

    PRICE_SELECTORS = [
        "[data-testid='price']",
        ".product-price",
        ".price",
        "[itemprop='price']",
        ".a-price-whole",  # Amazon
        ".price-current",
        "span.money",
        ".a-offscreen",  # Amazon screen reader price
    ]

    LINK_SELECTORS = [
        "a[href*='/product']",
        "a[href*='/dp/']",  # Amazon
        "a[href*='/p/']",
        ".product-card a",
        ".product-link",
        "h2 a",
    ]

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the scraper.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self._browser = None
        self._playwright = None

    async def _get_browser(self):
        """Get or create browser instance."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
        return self._browser

    async def close(self) -> None:
        """Close browser instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _find_products_on_page(self, page) -> list[dict]:
        """Extract products from a page using pattern matching."""
        products = []

        # Try each product selector pattern
        for product_selector in self.PRODUCT_SELECTORS:
            try:
                product_elements = await page.query_selector_all(product_selector)
                if product_elements:
                    _log(f"Found {len(product_elements)} products with {product_selector}")

                    for elem in product_elements[:10]:  # Limit to 10 products
                        product = await self._extract_product_data(elem, page.url)
                        if product:
                            products.append(product)

                    if products:
                        break  # Stop if we found products

            except Exception as e:
                _log(f"Selector {product_selector} failed: {e}")
                continue

        return products

    async def _extract_product_data(self, element, base_url: str) -> Optional[dict]:
        """Extract product data from a product card element."""
        try:
            # Extract title
            title = None
            for selector in self.TITLE_SELECTORS:
                try:
                    title_elem = await element.query_selector(selector)
                    if title_elem:
                        title = await title_elem.inner_text()
                        if title and title.strip():
                            break
                except Exception:
                    continue

            if not title:
                try:
                    title = await element.inner_text()
                    title = title.split("\n")[0][:100]  # First line, truncated
                except Exception:
                    title = "Unknown Product"

            # Extract price
            price = 0.0
            for selector in self.PRICE_SELECTORS:
                try:
                    price_elem = await element.query_selector(selector)
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        # Parse price (remove currency symbols, etc.)
                        price_text = price_text.replace("$", "").replace(",", "").strip()
                        try:
                            # Try to extract first number
                            import re
                            match = re.search(r'[\d.]+', price_text)
                            if match:
                                price = float(match.group())
                                break
                        except (ValueError, IndexError):
                            pass
                except Exception:
                    continue

            # Extract link
            url = None
            for selector in self.LINK_SELECTORS:
                try:
                    link_elem = await element.query_selector(selector)
                    if link_elem:
                        url = await link_elem.get_attribute("href")
                        if url and not url.startswith("http"):
                            # Handle relative URLs
                            from urllib.parse import urljoin
                            url = urljoin(base_url, url)
                        if url:
                            break
                except Exception:
                    continue

            if not url:
                try:
                    link = await element.query_selector("a")
                    if link:
                        url = await link.get_attribute("href")
                        if url and not url.startswith("http"):
                            from urllib.parse import urljoin
                            url = urljoin(base_url, url)
                except Exception:
                    url = base_url

            # Generate product ID
            product_id = hashlib.md5(f"{base_url}:{title}".encode()).hexdigest()[:12]

            # Extract retailer name
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            retailer = parsed.netloc.replace("www.", "")

            return {
                "id": product_id,
                "name": title.strip() if title else "Unknown Product",
                "price": price,
                "currency": "USD",
                "url": url or base_url,
                "image_url": None,  # Could extract img src
                "retailer": retailer,
                "in_stock": True  # Would need stock indicator detection
            }

        except Exception as e:
            _log(f"Failed to extract product data: {e}")
            return None

    async def search_products(
        self,
        retailer_url: str,
        query: str,
        max_price: Optional[float] = None
    ) -> list[dict]:
        """
        Search for products on a retailer website.

        Args:
            retailer_url: Base retailer URL
            query: Search query
            max_price: Optional maximum price filter

        Returns:
            List of product dicts
        """
        _log(f"Starting scrape of {retailer_url} for '{query}'")

        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            # Construct search URL (common patterns)
            from urllib.parse import quote_plus
            encoded_query = quote_plus(query)

            search_urls = [
                f"{retailer_url}/search?q={encoded_query}",
                f"{retailer_url}/s?k={encoded_query}",  # Amazon
                f"{retailer_url}/search?query={encoded_query}",
                f"{retailer_url}/search/{encoded_query}",
                f"{retailer_url}/shop/search?q={encoded_query}",
            ]

            products = []

            for search_url in search_urls:
                try:
                    _log(f"Trying: {search_url}")
                    await page.goto(search_url, timeout=self.timeout)
                    await page.wait_for_load_state("networkidle", timeout=10000)

                    products = await self._find_products_on_page(page)
                    if products:
                        break

                except Exception as e:
                    _log(f"Failed to load {search_url}: {e}")
                    continue

            # Apply price filter
            if max_price and products:
                products = [p for p in products if p["price"] <= max_price or p["price"] == 0]

            _log(f"Found {len(products)} products")
            return products

        finally:
            await page.close()
            await self.close()
