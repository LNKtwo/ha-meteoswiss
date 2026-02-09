"""MeteoSwiss API client."""
from __future__ import annotations

import aiohttp
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class MeteoSwissClient:
    """MeteoSwiss API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        hass: HomeAssistant | None = None,
        entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize."""
        self._session = session
        self._hass = hass
        self._entry = entry

        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close client session."""
        if self._session:
            await self._session.close()
            self._session = None
