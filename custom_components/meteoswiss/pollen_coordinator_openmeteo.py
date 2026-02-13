"""Pollen data coordinator using Open-Meteo Air Quality API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_current_weather_cache
from .const import CONF_POSTAL_CODE, DOMAIN, MIN_UPDATE_INTERVAL
from .retry import async_retry_with_backoff

_LOGGER = logging.getLogger(__name__)

# Open-Meteo Air Quality API
OPENMETEO_AQ_BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Pollen types
POLLEN_ALDER = "alder_pollen"
POLLEN_BIRCH = "birch_pollen"
POLLEN_GRASS = "grass_pollen"
POLLEN_MUGWORT = "mugwort_pollen"
POLLEN_RAGWEED = "ragweed_pollen"

# Pollen types list
POLLEN_TYPES = [
    POLLEN_ALDER,
    POLLEN_BIRCH,
    POLLEN_GRASS,
    POLLEN_MUGWORT,
    POLLEN_RAGWEED,
]


class OpenMeteoPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching pollen data from Open-Meteo Air Quality API."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        update_interval: int = 1800,  # 30 minutes default
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self._session = session

        # Ensure minimum update interval
        if update_interval < MIN_UPDATE_INTERVAL:
            _LOGGER.warning(
                "Update interval %s is below minimum %s, using minimum",
                update_interval,
                MIN_UPDATE_INTERVAL,
            )
            update_interval = MIN_UPDATE_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_pollen",
            update_interval=timedelta(seconds=update_interval),
        )

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_fetch_data(self) -> dict[str, Any] | None:
        """Fetch data from Open-Meteo Air Quality API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        # Build API URL with pollen variables
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": ",".join(POLLEN_TYPES),
            "forecast_days": 5,
            "timezone": "Europe/Zurich",
        }

        try:
            _LOGGER.info(
                "Fetching Open-Meteo Air Quality data for lat=%s, lon=%s",
                self.latitude,
                self.longitude,
            )

            async with self._session.get(OPENMETEO_AQ_BASE_URL, params=params) as response:
                if response.status != 200:
                    _LOGGER.error("Open-Meteo AQ API error: %s", response.status)
                    return None

                data = await response.json()
                _LOGGER.debug("Open-Meteo AQ response keys: %s", data.keys())

                return self._parse_response(data)

        except aiohttp.ClientError as err:
            _LOGGER.error("Open-Meteo AQ API request failed: %s", err)
            return None
        except Exception as err:
            _LOGGER.error("Error fetching Open-Meteo AQ data: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            return None

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Open-Meteo Air Quality API response."""
        try:
            result = {
                POLLEN_ALDER: None,
                POLLEN_BIRCH: None,
                POLLEN_GRASS: None,
                POLLEN_MUGWORT: None,
                POLLEN_RAGWEED: None,
                "last_update": None,
            }

            # Parse hourly data
            hourly = data.get("hourly", {})
            hourly_time = hourly.get("time", [])

            # Parse each pollen type
            for pollen_type in POLLEN_TYPES:
                pollen_values = hourly.get(pollen_type, [])

                if pollen_values and len(pollen_values) > 0:
                    # Get most recent value (current)
                    result[pollen_type] = {
                        "current": float(pollen_values[0]) if pollen_values[0] is not None else 0,
                        "unit": "Grains/m³",
                        "forecast": pollen_values[:24] if len(pollen_values) > 0 else [],  # Next 24 hours
                    }
                    _LOGGER.debug(
                        "Parsed %s: current=%s, forecast_hours=%d",
                        pollen_type,
                        result[pollen_type]["current"],
                        len(result[pollen_type]["forecast"]),
                    )

            # Parse timestamp
            if hourly_time and len(hourly_time) > 0:
                result["last_update"] = hourly_time[0]
                _LOGGER.debug("Pollen timestamp: %s", result["last_update"])

            # Check if we have any data
            has_data = any(
                result.get(pt) is not None for pt in POLLEN_TYPES
            )

            if not has_data:
                _LOGGER.warning("No pollen data available (possibly outside pollen season)")
                return {}

            _LOGGER.info("✅ Successfully parsed pollen data")

            return result

        except Exception as err:
            _LOGGER.error("Error parsing Open-Meteo AQ response: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with caching."""
        _LOGGER.info("=== FETCHING POLLEN DATA (lat=%s, lon=%s) ===", self.latitude, self.longitude)

        # Get cache
        cache = get_current_weather_cache()
        cache_key = f"pollen:{self.latitude},{self.longitude}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            _LOGGER.info("✅ Using cached pollen data")
            return cached_data

        _LOGGER.info("❌ Cache miss, fetching fresh pollen data")

        data = await self._async_fetch_data()

        if data is None:
            _LOGGER.error("Pollen data is None!")
            raise UpdateFailed("Failed to fetch pollen data: data is None")

        if not data:
            _LOGGER.error("Pollen data is empty!")
            raise UpdateFailed("Failed to fetch pollen data: data is empty")

        _LOGGER.info("✅ Successfully fetched pollen data")

        # Cache result (TTL: 1800s = 30 min for pollen)
        cache.set(cache_key, data, ttl=1800.0)
        _LOGGER.info("✅ Cached pollen data (TTL: 1800s)")

        _LOGGER.info("=== POLLEN FETCH COMPLETE ===")

        return data

    async def async_close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
