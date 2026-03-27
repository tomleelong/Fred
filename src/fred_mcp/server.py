"""FastMCP server exposing FRED (Federal Reserve Economic Data) API tools."""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastmcp import Context, FastMCP

from .client import FredClient
from .config import FredSettings

# Configure logging to stderr (critical for stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def _get_client(ctx: Context) -> FredClient:
    """Extract FredClient from the lifespan context."""
    client = ctx.lifespan_context.get("client")
    if client is None:
        raise RuntimeError(
            "FRED client is not available. "
            "Check server logs for initialization errors (missing FRED_API_KEY?)."
        )
    return client


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Initialize the FRED HTTP client on server startup."""
    logger.info("Starting FRED MCP server...")
    try:
        settings = FredSettings()
    except Exception as e:
        logger.error("Failed to load FRED settings: %s", e)
        raise RuntimeError(
            f"Failed to load configuration: {e}. "
            "Ensure FRED_API_KEY is set in your environment or .env file."
        ) from e

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        client = FredClient(settings, http_client)
        logger.info("FRED client initialized successfully")
        yield {"client": client}

    logger.info("FRED MCP server stopped")


mcp = FastMCP(
    "FRED MCP",
    instructions=(
        "Access Federal Reserve Economic Data (FRED). "
        "Search for economic series, retrieve time series observations, "
        "and browse the FRED category hierarchy."
    ),
    lifespan=app_lifespan,
)


# --- Tools ---


@mcp.tool
async def search_series(
    query: str,
    ctx: Context,
    limit: int = 10,
) -> str:
    """Search FRED for economic data series by keyword.

    Args:
        query: Search terms (e.g. "GDP", "unemployment rate", "consumer price index").
        limit: Max number of results to return (default 10, max 1000).

    Returns:
        Matching series with IDs, titles, frequency, units, and date ranges.
    """
    client = _get_client(ctx)
    data = await client.search_series(query, limit=limit)
    series_list = data.get("seriess", [])

    if not series_list:
        return f"No series found for '{query}'."

    lines = [f"Found {data.get('count', len(series_list))} series (showing {len(series_list)}):\n"]
    for s in series_list:
        lines.append(
            f"- **{s['id']}**: {s['title']}\n"
            f"  Frequency: {s.get('frequency', 'N/A')} | "
            f"Units: {s.get('units', 'N/A')} | "
            f"Seasonal: {s.get('seasonal_adjustment', 'N/A')}\n"
            f"  Range: {s.get('observation_start', '?')} to {s.get('observation_end', '?')}"
        )
    return "\n".join(lines)


@mcp.tool
async def get_series(
    series_id: str,
    ctx: Context,
) -> str:
    """Get metadata for a specific FRED series.

    Args:
        series_id: FRED series ID (e.g. "GDP", "UNRATE", "CPIAUCSL", "DFF", "SP500").

    Returns:
        Series metadata including title, units, frequency, and date range.
    """
    client = _get_client(ctx)
    data = await client.get_series(series_id)
    series_list = data.get("seriess", [])

    if not series_list:
        return f"Series '{series_id}' not found."

    s = series_list[0]
    return (
        f"**{s['id']}**: {s['title']}\n\n"
        f"- Frequency: {s.get('frequency', 'N/A')}\n"
        f"- Units: {s.get('units', 'N/A')}\n"
        f"- Seasonal adjustment: {s.get('seasonal_adjustment', 'N/A')}\n"
        f"- Observation range: {s.get('observation_start', '?')} to {s.get('observation_end', '?')}\n"
        f"- Last updated: {s.get('last_updated', 'N/A')}\n"
        f"- Notes: {s.get('notes', 'N/A')[:500]}"
    )


@mcp.tool
async def get_observations(
    series_id: str,
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
    frequency: str | None = None,
    units: str | None = None,
    limit: int = 100,
    sort_order: str = "desc",
) -> str:
    """Get time series observations (data points) for a FRED series.

    Args:
        series_id: FRED series ID (e.g. "GDP", "UNRATE").
        start_date: Start date in YYYY-MM-DD format (optional).
        end_date: End date in YYYY-MM-DD format (optional).
        frequency: Aggregation frequency — d, w, bw, m, q, sa, a (optional).
        units: Data transformation — lin (default), chg, ch1, pch, pc1, pca, cch, cca, log (optional).
        limit: Max observations to return (default 100, max 100000).
        sort_order: "asc" (oldest first) or "desc" (newest first, default).

    Returns:
        Formatted table of date/value observations.
    """
    client = _get_client(ctx)
    data = await client.get_observations(
        series_id,
        observation_start=start_date,
        observation_end=end_date,
        frequency=frequency,
        units=units,
        limit=limit,
        sort_order=sort_order,
    )

    observations = data.get("observations", [])
    if not observations:
        return f"No observations found for '{series_id}'."

    count = data.get("count", len(observations))
    lines = [
        f"**{series_id}** — {count} total observations (showing {len(observations)}):\n",
        "| Date | Value |",
        "|------|-------|",
    ]
    for obs in observations:
        lines.append(f"| {obs['date']} | {obs['value']} |")

    return "\n".join(lines)


@mcp.tool
async def get_category(
    ctx: Context,
    category_id: int = 0,
) -> str:
    """Get information about a FRED category.

    The root category (id=0) contains all top-level categories.

    Args:
        category_id: FRED category ID (default 0 for root).

    Returns:
        Category name, ID, and parent ID.
    """
    client = _get_client(ctx)
    data = await client.get_category(category_id)
    categories = data.get("categories", [])

    if not categories:
        return f"Category {category_id} not found."

    cat = categories[0]
    return (
        f"**Category {cat['id']}**: {cat['name']}\n"
        f"- Parent ID: {cat.get('parent_id', 'N/A')}"
    )


@mcp.tool
async def get_category_children(
    ctx: Context,
    category_id: int = 0,
) -> str:
    """List child categories within a FRED category.

    Start with category_id=0 to see all top-level categories,
    then drill down into subcategories.

    Args:
        category_id: Parent category ID (default 0 for root).

    Returns:
        List of child categories with IDs and names.
    """
    client = _get_client(ctx)
    data = await client.get_category_children(category_id)
    categories = data.get("categories", [])

    if not categories:
        return f"No child categories found for category {category_id}."

    lines = [f"Children of category {category_id}:\n"]
    for cat in categories:
        lines.append(f"- **{cat['id']}**: {cat['name']}")

    return "\n".join(lines)


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
