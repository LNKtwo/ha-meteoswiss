"""MeteoSwiss API client."""
from __future__ import annotations

import aiohttp


class MeteoSwissClient:
    """MeteoSwiss API client."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize."""
        self._session = session
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close client session."""
        if self._session:
            await self._session.close()
            self._session = None
