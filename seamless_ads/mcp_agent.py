"""MCP Product Discovery Agent.

Connects to an MCP server and calls discover_product for each unique product
found in a structured_products JSON file.
"""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, MofNCompleteColumn
from rich.table import Table

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

CONTENT_FILE_MAP: dict[str, str] = {
    "1": "STS3E4_structured_products.json",
    "2": "BBS3E2_structured_products.json",
}


def load_unique_products(content_id: str) -> list[dict[str, Any]]:
    """Load structured products JSON and return deduplicated product list sorted by frequency."""
    filename = CONTENT_FILE_MAP.get(content_id)
    if not filename:
        raise ValueError(f"Unknown content_id: {content_id}")

    filepath = OUTPUTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Structured products file not found: {filepath}")

    with open(filepath) as f:
        data = json.load(f)

    # Count occurrences of each product_name across all scenes
    name_counter: Counter[str] = Counter()
    product_info: dict[str, dict[str, Any]] = {}

    for scene in data.get("scenes", []):
        for mention in scene.get("product_mentions", []):
            name = mention.get("product_name", "").strip()
            if not name:
                continue
            name_counter[name] += 1
            # Keep the first occurrence's metadata
            if name not in product_info:
                product_info[name] = {
                    "product_name": name,
                    "brand": mention.get("brand", "Unknown"),
                    "category": mention.get("category", "Unknown"),
                }

    # Build result sorted by frequency (most common first)
    results = []
    for name, count in name_counter.most_common():
        info = product_info[name]
        info["scene_count"] = count
        results.append(info)

    return results


async def run_discovery(content_id: str, mcp_url: str = "http://localhost:8000/mcp") -> None:
    """Connect to MCP server and discover products sequentially."""
    console = Console()
    filename = CONTENT_FILE_MAP.get(content_id, "unknown")

    products = load_unique_products(content_id)
    unique_count = len(products)

    # Header panel
    console.print()
    console.print(Panel(
        f"[bold cyan]Seamless Product Discovery Agent[/bold cyan]\n"
        f"Content: [yellow]{content_id}[/yellow] | File: [yellow]{filename}[/yellow]\n"
        f"Unique products: [green]{unique_count}[/green] | MCP: [blue]{mcp_url}[/blue]",
        border_style="bright_cyan",
    ))

    # Connect to MCP server
    async with streamablehttp_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Verify tools
            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            console.print(f"\nConnected to MCP server. Tools: [green]{tool_names}[/green]\n")

            if "discover_product" not in tool_names:
                console.print("[bold red]Error: discover_product tool not found on MCP server[/bold red]")
                return

            # Results storage
            found_count = 0
            not_found_count = 0
            error_count = 0

            # Build results table
            table = Table(show_header=True, header_style="bold magenta", border_style="dim")
            table.add_column("Product", style="white", min_width=18)
            table.add_column("Brand/Cat", style="cyan", min_width=14)
            table.add_column("Scenes", style="yellow", justify="right", min_width=6)
            table.add_column("Kroger Match", style="green", min_width=22)
            table.add_column("Price", style="white", justify="right", min_width=8)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Discovering products...", total=unique_count)

                for product in products:
                    name = product["product_name"]
                    brand_cat = f"{product['brand']}/{product['category']}"
                    scenes = str(product["scene_count"])

                    try:
                        result = await session.call_tool(
                            "discover_product",
                            arguments={"query": name, "max_results": 1},
                        )

                        # Parse the tool result
                        kroger_match = "No results"
                        price = "-"
                        match_style = "dim"

                        if result.content:
                            text_content = ""
                            for block in result.content:
                                if hasattr(block, "text"):
                                    text_content += block.text

                            if text_content.strip():
                                try:
                                    parsed = json.loads(text_content)
                                    # Handle both list and dict responses
                                    items = parsed if isinstance(parsed, list) else parsed.get("products", parsed.get("items", []))
                                    if isinstance(items, list) and len(items) > 0:
                                        item = items[0]
                                        kroger_match = item.get("description", item.get("name", "Found"))[:30]
                                        raw_price = item.get("price", item.get("regular_price"))
                                        if raw_price is not None:
                                            price = f"${float(raw_price):.2f}"
                                        found_count += 1
                                        match_style = "green"
                                    elif isinstance(items, dict) and items:
                                        kroger_match = items.get("description", items.get("name", "Found"))[:30]
                                        raw_price = items.get("price", items.get("regular_price"))
                                        if raw_price is not None:
                                            price = f"${float(raw_price):.2f}"
                                        found_count += 1
                                        match_style = "green"
                                    else:
                                        not_found_count += 1
                                except (json.JSONDecodeError, ValueError, TypeError):
                                    # Non-JSON response — treat as a descriptive match
                                    if "no results" in text_content.lower() or "not found" in text_content.lower():
                                        not_found_count += 1
                                    else:
                                        kroger_match = text_content.strip()[:30]
                                        found_count += 1
                                        match_style = "green"
                            else:
                                not_found_count += 1
                        else:
                            not_found_count += 1

                        table.add_row(
                            name[:18],
                            brand_cat[:14],
                            scenes,
                            f"[{match_style}]{kroger_match}[/{match_style}]",
                            price,
                        )

                    except Exception as e:
                        error_count += 1
                        table.add_row(
                            name[:18],
                            brand_cat[:14],
                            scenes,
                            f"[red]Error: {str(e)[:20]}[/red]",
                            "-",
                        )

                    progress.advance(task)

            # Print results
            console.print()
            console.print(table)
            console.print()

            # Summary panel
            console.print(Panel(
                f"[green]Found: {found_count}[/green] | "
                f"[yellow]Not found: {not_found_count}[/yellow] | "
                f"[red]Errors: {error_count}[/red]",
                border_style="bright_cyan",
            ))
