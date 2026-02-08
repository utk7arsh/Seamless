"""Web search tool using DuckDuckGo.

Provides web search functionality to find retailers and shopping sites.
"""

import sys
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _log(message: str) -> None:
    """Log to stderr to avoid corrupting STDIO transport."""
    print(f"[web_search] {message}", file=sys.stderr)


def web_search(
    query: str,
    max_results: int = 10,
    region: Optional[str] = None
) -> list[dict]:
    """
    Search the web for retailers matching the query.

    Uses DuckDuckGo search to find relevant shopping sites and retailers.

    Args:
        query: Search query string (e.g., "buy headphones online")
        max_results: Maximum number of results to return (default: 10)
        region: Optional region code (e.g., "us-en", "uk-en")

    Returns:
        List of dicts with keys: title, url, description
    """
    _log(f"Searching for: {query}")

    # Get defaults from environment
    if max_results is None:
        max_results = int(os.getenv("SEARCH_MAX_RESULTS", "10"))
    if region is None:
        region = os.getenv("SEARCH_REGION", "wt-wt")

    try:
        from duckduckgo_search import DDGS

        ddgs = DDGS(timeout=10)
        results = ddgs.text(
            keywords=query,
            region=region,
            safesearch="moderate",
            max_results=max_results
        )

        search_results = []
        for r in results:
            search_results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "description": r.get("body", "")
            })

        _log(f"Found {len(search_results)} results")
        return search_results

    except ImportError:
        _log("duckduckgo-search not installed, returning mock results")
        return _mock_search_results(query, max_results)
    except Exception as e:
        _log(f"Error during search: {e}")
        # Return mock results as fallback
        return _mock_search_results(query, max_results)


def _mock_search_results(query: str, max_results: int) -> list[dict]:
    """Generate mock search results for demo/fallback."""
    mock_retailers = [
        {
            "title": f"Amazon.com: {query}",
            "url": f"https://www.amazon.com/s?k={query.replace(' ', '+')}",
            "description": f"Shop for {query} on Amazon. Free shipping on eligible orders."
        },
        {
            "title": f"Best Buy: {query}",
            "url": f"https://www.bestbuy.com/site/searchpage.jsp?st={query.replace(' ', '+')}",
            "description": f"Find great deals on {query} at Best Buy. Shop online or in-store."
        },
        {
            "title": f"Walmart.com: {query}",
            "url": f"https://www.walmart.com/search?q={query.replace(' ', '+')}",
            "description": f"Save money on {query}. Free pickup and delivery available."
        },
        {
            "title": f"Target: {query}",
            "url": f"https://www.target.com/s?searchTerm={query.replace(' ', '+')}",
            "description": f"Shop {query} at Target. Free shipping on orders over $35."
        },
        {
            "title": f"eBay: {query}",
            "url": f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}",
            "description": f"Find great deals on {query}. Shop with confidence on eBay."
        },
    ]
    return mock_retailers[:max_results]
