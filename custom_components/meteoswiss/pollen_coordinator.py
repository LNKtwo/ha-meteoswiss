"""Pollen data coordinator for MeteoSwiss integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_POSTAL_CODE, DOMAIN
from .pollen import MeteoSwissPollenAPI

_LOGGER = logging.getLogger(__name__)


class MeteoSwissPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching pollen data from MeteoSwiss."""

    def __init__(
        self,
        hass: HomeAssistant,
        pollen_api: MeteoSwissPollenAPI,
        postal_code: str,
        update_interval: int = 1800,
    ) -> None:
        """Initialize."""
        self._pollen_api = pollen_api
        self._postal_code = postal_code

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_pollen",
            update_interval=timedelta(minutes=30),  # Pollen updates every 30 minutes
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch pollen data from MeteoSwiss."""
        _LOGGER.info("Fetching pollen data for postal code %s", self._postal_code)

        try:
            pollen_data = await self._pollen_api.get_pollen_data(self._postal_code)

            if not pollen_data:
                _LOGGER.warning("No pollen data available for %s", self._postal_code)
                return {}

            _LOGGER.info("Successfully fetched pollen data: %d types", len(pollen_data))
            return pollen_data

        except Exception as err:
            _LOGGER.error("Error fetching pollen data: %s", err)
            raise UpdateFailed(f"Failed to fetch pollen data: {err}")

    async def async_close(self) -> None:
        """Close pollen API session."""
        await self._pollen_api.close()
