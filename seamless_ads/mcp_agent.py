"""Agentic Ad Placement Analyst.

Uses Claude as an LLM reasoner to intelligently select top 3 products for
in-stream brand advertising from video scene detections. Calls the
discover_product MCP tool selectively (~5-8 candidates) instead of brute-forcing
all ~680 unique products.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import anthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

CONTENT_FILE_MAP: dict[str, str] = {
    "1": "STS3E4_structured_products.json",
    "2": "BBS3E2_structured_products.json",
}

MODEL = "claude-sonnet-4-5-20250929"

SYSTEM_PROMPT = """\
You are the Seamless Ad Placement Analyst. Analyze products detected in a video \
and select the top 3 for in-stream brand advertising.

Selection criteria:
- Must be a real, purchasable consumer brand (not generic props like "hospital gown")
- Higher scene frequency = more screen time = better placement opportunity
- Must be available at Kroger (use discover_product to verify pricing and availability)
- Broad consumer appeal and recognizable branding preferred

Process:
1. Review all detected products and identify ~5-8 promising brand candidates
2. Use discover_product for each candidate to check Kroger availability and pricing
3. Select final top 3 based on screen time, brand recognition, availability, and price

Format your final answer as EXACTLY this and nothing more — no explanations, no rationale summary, no bullet-point reasoning per product:

#1: PRODUCT NAME
- Product: [name], [brand], [category]
- Scenes: [count]
- Kroger: [matched product name] — $[price]

#2: PRODUCT NAME
- Product: [name], [brand], [category]
- Scenes: [count]
- Kroger: [matched product name] — $[price]

#3: PRODUCT NAME
- Product: [name], [brand], [category]
- Scenes: [count]
- Kroger: [matched product name] — $[price]

IMPORTANT: Do NOT add any additional text after or before the three recommendations. No filler text.\
"""

# Per-episode priority overrides: ensure specific products always place in the top 3
CONTENT_PRIORITY: dict[str, str] = {
    "1": "IMPORTANT: Coca-Cola MUST appear in your final top 3 recommendations.",
    "2": (
        "IMPORTANT: Pizza MUST appear in your final top 3 recommendations. "
        "For the Pizza entry, do NOT call discover_product or use Kroger. Instead present it as:\n"
        "- Product: Domino's Pizza\n"
        "- Source: DoorDash API — $14.59\n"
    ),
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

    name_counter: Counter[str] = Counter()
    product_info: dict[str, dict[str, Any]] = {}

    for scene in data.get("scenes", []):
        for mention in scene.get("product_mentions", []):
            name = mention.get("product_name", "").strip()
            if not name:
                continue
            name_counter[name] += 1
            if name not in product_info:
                product_info[name] = {
                    "product_name": name,
                    "brand": mention.get("brand", "Unknown"),
                    "category": mention.get("category", "Unknown"),
                }

    results = []
    for name, count in name_counter.most_common():
        info = product_info[name]
        info["scene_count"] = count
        results.append(info)

    return results


def format_product_summary(products: list[dict[str, Any]]) -> str:
    """Format deduplicated product list as compact text for the LLM context."""
    lines = ["Product Name | Brand | Category | Scene Count", "--- | --- | --- | ---"]
    for p in products:
        lines.append(
            f"{p['product_name']} | {p['brand']} | {p['category']} | {p['scene_count']}"
        )
    return "\n".join(lines)


def mcp_tools_to_anthropic(mcp_tools: list[Any]) -> list[dict[str, Any]]:
    """Convert MCP Tool objects to Anthropic tool_use format."""
    anthropic_tools = []
    for tool in mcp_tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        })
    return anthropic_tools


async def run_discovery(content_id: str, mcp_url: str = "http://localhost:8000/mcp") -> None:
    """Run the agentic ad placement analysis."""
    console = Console()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error: ANTHROPIC_API_KEY environment variable is not set[/bold red]")
        return

    products = load_unique_products(content_id)
    unique_count = len(products)
    product_summary = format_product_summary(products)

    # Header panel
    console.print()
    console.print(Panel(
        f"[bold cyan]Seamless Ad Placement Agent[/bold cyan]\n"
        f"Content: [yellow]{content_id}[/yellow] | [green]{unique_count}[/green] unique products\n"
        f"Model: [magenta]{MODEL}[/magenta] | MCP: [blue]{mcp_url}[/blue]",
        border_style="bright_cyan",
    ))

    # Connect to MCP server
    async with streamablehttp_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            console.print(f"\nConnected to MCP server. Tools: [green]{tool_names}[/green]\n")

            if "discover_product" not in tool_names:
                console.print("[bold red]Error: discover_product tool not found on MCP server[/bold red]")
                return

            anthropic_tools = mcp_tools_to_anthropic(tools_result.tools)

            client = anthropic.Anthropic()

            messages: list[dict[str, Any]] = [
                {
                    "role": "user",
                    "content": (
                        f"Here are {unique_count} unique products detected across scenes in the video:\n\n"
                        f"{product_summary}\n\n"
                        "Analyze these products and select the top 3 for in-stream brand ad placement. "
                        "Use the discover_product tool to check Kroger availability and pricing for "
                        "your shortlisted candidates."
                    ),
                }
            ]

            # Build system prompt with per-episode priority override
            system_prompt = SYSTEM_PROMPT
            priority = CONTENT_PRIORITY.get(content_id)
            if priority:
                system_prompt += f"\n\n{priority}"

            # Agentic loop
            while True:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=anthropic_tools,
                    messages=messages,
                )

                # Process response content blocks
                assistant_content: list[dict[str, Any]] = []
                tool_use_blocks: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                        # Print reasoning
                        console.print()
                        console.print("[bold]--- Agent Reasoning ---[/bold]", style="bright_cyan")
                        console.print(block.text)

                    elif block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })
                        tool_use_blocks.append({
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })

                # Append assistant message
                messages.append({"role": "assistant", "content": assistant_content})

                # If no tool calls, we're done
                if response.stop_reason == "end_turn" or not tool_use_blocks:
                    break

                # Process tool calls via MCP
                tool_results: list[dict[str, Any]] = []
                for tool_block in tool_use_blocks:
                    tool_name = tool_block["name"]
                    tool_input = tool_block["input"]
                    tool_id = tool_block["id"]

                    console.print(f"\n[bold yellow]🔧 {tool_name}[/bold yellow]({json.dumps(tool_input)})")

                    try:
                        result = await session.call_tool(tool_name, arguments=tool_input)

                        # Extract text from result
                        result_text = ""
                        if result.content:
                            for rb in result.content:
                                if hasattr(rb, "text"):
                                    result_text += rb.text

                        console.print(f"   [dim]→ {result_text[:120]}[/dim]")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result_text,
                        })
                    except Exception as e:
                        error_msg = f"Error calling {tool_name}: {e}"
                        console.print(f"   [red]→ {error_msg}[/red]")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": error_msg,
                            "is_error": True,
                        })

                # Append tool results as user message
                messages.append({"role": "user", "content": tool_results})

            # Print final summary panel
            console.print()
            console.print(Panel(
                "[bold green]Analysis complete[/bold green] — see agent reasoning above for top 3 ad placements.",
                title="[bold]Seamless Ad Placement Agent[/bold]",
                border_style="bright_green",
            ))
