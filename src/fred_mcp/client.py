"""FRED API HTTP client wrapping httpx.AsyncClient."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from fred_mcp.config import FredSettings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stlouisfed.org/fred"


class FredAPIError(Exception):
    """Raised when the FRED API returns a non-200 response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"FRED API error ({status_code}): {message}")


class FredClient:
    """Async HTTP client for the FRED API.

    Args:
        settings: FRED configuration with API key.
        http_client: Shared httpx.AsyncClient instance.
    """

    def __init__(self, settings: FredSettings, http_client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http_client
        self._base_url = settings.base_url

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to the FRED API.

        Auto-injects api_key and file_type=json on every request.
        """
        request_params: dict[str, Any] = {
            "api_key": self._settings.api_key,
            "file_type": "json",
        }
        if params:
            request_params.update(params)

        url = f"{self._base_url}{path}"
        logger.debug("GET %s", url)

        response = await self._http.get(url, params=request_params)
        if response.status_code != 200:
            error_msg = response.text[:500]
            if response.status_code == 429:
                logger.warning("FRED API rate limit hit (120 req/min)")
            raise FredAPIError(response.status_code, error_msg)

        return response.json()

    # --- Series endpoints ---

    async def get_series(self, series_id: str) -> dict[str, Any]:
        """Get metadata for a FRED series."""
        return await self._get("/series", {"series_id": series_id})

    async def get_observations(
        self,
        series_id: str,
        observation_start: str | None = None,
        observation_end: str | None = None,
        frequency: str | None = None,
        units: str | None = None,
        limit: int | None = None,
        sort_order: str | None = None,
    ) -> dict[str, Any]:
        """Get observations (data points) for a FRED series."""
        params: dict[str, Any] = {"series_id": series_id}
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        if frequency:
            params["frequency"] = frequency
        if units:
            params["units"] = units
        if limit is not None:
            params["limit"] = limit
        if sort_order:
            params["sort_order"] = sort_order
        return await self._get("/series/observations", params)

    # --- Search endpoints ---

    async def search_series(
        self,
        search_text: str,
        limit: int = 10,
        order_by: str | None = None,
    ) -> dict[str, Any]:
        """Search for FRED series by text."""
        params: dict[str, Any] = {
            "search_text": search_text,
            "limit": limit,
        }
        if order_by:
            params["order_by"] = order_by
        return await self._get("/series/search", params)

    # --- Category endpoints ---

    async def get_category(self, category_id: int = 0) -> dict[str, Any]:
        """Get info about a FRED category. Root category is 0."""
        return await self._get("/category", {"category_id": category_id})

    async def get_category_children(self, category_id: int = 0) -> dict[str, Any]:
        """Get child categories of a FRED category."""
        return await self._get("/category/children", {"category_id": category_id})
