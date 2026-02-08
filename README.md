# Shopping Agent MCP Server

A Model Context Protocol (MCP) server that provides shopping assistance tools for AI agents. Built for the hackathon using Dedalus Labs infrastructure.

## Features

- **Web Search**: Search the web for retailers and shopping sites using DuckDuckGo
- **Product Search**: Search for products on specific retailer websites with price filtering
- **Cart Management**: Add items to cart, view cart contents
- **Mock Checkout**: Simulate the checkout process (no real transactions)

## Requirements

- Python 3.10+
- Playwright (for product scraping when not in demo mode)

## Quick Start

### 1. Clone and Setup

```bash
cd demomcpdeadalus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Playwright Browsers (Optional)

Only needed if you want to use real web scraping (DEMO_MODE=false):

```bash
playwright install chromium
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env as needed
```

### 4. Run Tests

```bash
python test_server.py
```

### 5. Run the Server

```bash
python server.py
```

The server runs on HTTP transport at `http://localhost:8000`. You should see output like:

```
[2024-01-15 10:30:00] INFO - shopping-agent - Starting Shopping Agent MCP Server...
[2024-01-15 10:30:00] INFO - shopping-agent - Tools registered: web_search, search_products, add_to_cart, view_cart, mock_checkout
[2024-01-15 10:30:00] INFO - shopping-agent - Starting HTTP server on port 8000...
```

## Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `web_search` | Search web for retailers | `query` (required), `max_results`, `region` |
| `search_products` | Search products on a site | `retailer_url` (required), `query` (required), `max_price` |
| `add_to_cart` | Add product to cart | `product_id` (required), `quantity` |
| `view_cart` | View cart contents | None |
| `mock_checkout` | Simulate checkout | `cart_id` (required) |

## Integration with Claude Desktop

**Important**: The server must be running before Claude connects. Start the server first with `python server.py`.

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "shopping-agent": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Testing the Server

### Test with curl

Once the server is running, you can test the MCP endpoint:

```bash
# Test the endpoint is reachable
curl http://localhost:8000/mcp
```

### Run Tool Tests

```bash
python test_server.py
```

## Project Structure

```
demomcpdeadalus/
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── server.py             # Main MCP server entry point
├── test_server.py        # Test script for tools
├── tools/
│   ├── __init__.py       # Tools package exports
│   ├── web_search.py     # DuckDuckGo web search
│   ├── product_search.py # Product scraping/mock data
│   └── cart_management.py # Cart state management
└── scrapers/
    ├── __init__.py       # Scrapers package exports
    └── generic_patterns.py # E-commerce CSS selector patterns
```

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEMO_MODE` | `true` | Use mock data instead of real scraping |
| `HEADLESS` | `true` | Run Playwright in headless mode |
| `BROWSER_TIMEOUT` | `30000` | Page load timeout in ms |
| `SEARCH_MAX_RESULTS` | `10` | Default max search results |
| `SEARCH_REGION` | `wt-wt` | DuckDuckGo region code |

## Demo Mode

By default, `DEMO_MODE=true` uses mock data instead of real web scraping. This is useful for:

- Local development and testing
- Hackathon demos without rate limiting issues
- Consistent, predictable responses

Set `DEMO_MODE=false` to enable actual Playwright-based scraping.

## Example Usage

Here's an example conversation flow:

1. **Find retailers**: "Search for stores that sell wireless headphones"
2. **Search products**: "Search Amazon for wireless headphones under $100"
3. **Add to cart**: "Add the budget option to my cart"
4. **View cart**: "What's in my cart?"
5. **Checkout**: "Complete the checkout"

## Architecture Notes

### HTTP Transport

The server uses HTTP transport via dedalus-mcp-python:
- **Endpoint**: `http://localhost:8000/mcp`
- **Protocol**: JSON-RPC over HTTP
- **Logging**: All logs go to stderr

### Cart State

Cart state is stored in-memory for simplicity. The cart:
- Persists during the server session
- Clears on server restart
- Supports multiple items with quantity tracking

### Product Cache

Products from searches are cached in-memory, allowing:
- Cart operations to reference product details by ID
- Price and name lookups without re-scraping

## Next Steps

- [ ] Add more retailer-specific scrapers
- [ ] Implement price comparison across retailers
- [ ] Add product detail view tool
- [ ] Deploy to Dedalus hosting
- [ ] Add persistent cart storage

## License

MIT
