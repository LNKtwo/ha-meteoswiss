"""Data update coordinator for MeteoSwiss."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE,
    DOMAIN,
    GRANULARITY_10MIN,
    MIN_UPDATE_INTERVAL,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_SPEED,
    STAC_COLLECTION,
)

_LOGGER = logging.getLogger(__name__)


class MeteoSwissDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from MeteoSwiss API."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        update_interval: int,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize."""
        self.station_id = station_id
        self.session = session
        self._last_update: datetime | None = None

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
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_get_station_data(self) -> dict[str, Any] | None:
        """Fetch current weather data for the station."""
        # STAC endpoint for station data
        url = f"{API_BASE}/collections/{STAC_COLLECTION}/items"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch station data: %s", response.status)
                    return None

                data = await response.json()

                # Find our station in the features
                for feature in data.get("features", []):
                    if feature.get("id") == self.station_id:
                        return feature.get("properties", {})

                _LOGGER.warning("Station %s not found in response", self.station_id)
                return None

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching station data")
            return None
        except Exception as err:
            _LOGGER.error("Error fetching station data: %s", err)
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        _LOGGER.debug("Fetching data for station %s", self.station_id)

        station_data = await self._async_get_station_data()

        if station_data is None:
            raise UpdateFailed("Failed to fetch station data")

        # Parse and normalize the data
        parsed_data = self._parse_station_data(station_data)

        if not parsed_data:
            raise UpdateFailed("No valid data received")

        self._last_update = datetime.now()
        _LOGGER.debug("Successfully updated data for station %s", self.station_id)

        return parsed_data

    def _parse_station_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse station data into a normalized format."""
        try:
            result = {
                SENSOR_TEMPERATURE: None,
                SENSOR_HUMIDITY: None,
                SENSOR_WIND_SPEED: None,
                SENSOR_WIND_DIRECTION: None,
                SENSOR_PRECIPITATION: None,
                SENSOR_PRESSURE: None,
            }

            # Extract values from MeteoSwiss data format
            # The data comes in a specific format that needs to be parsed
            # This is a simplified version - will need to be adjusted based on actual API response

            if "temperature" in data:
                result[SENSOR_TEMPERATURE] = float(data["temperature"])

            if "humidity" in data:
                result[SENSOR_HUMIDITY] = float(data["humidity"])

            if "wind_speed" in data:
                result[SENSOR_WIND_SPEED] = float(data["wind_speed"])

            if "wind_direction" in data:
                result[SENSOR_WIND_DIRECTION] = int(data["wind_direction"])

            if "precipitation" in data:
                result[SENSOR_PRECIPITATION] = float(data["precipitation"])

            if "pressure" in data:
                result[SENSOR_PRESSURE] = float(data["pressure"])

            # Add timestamp
            if "timestamp" in data:
                result["last_update"] = data["timestamp"]
            else:
                result["last_update"] = datetime.now().isoformat()

            return result

        except (ValueError, KeyError, TypeError) as err:
            _LOGGER.error("Error parsing station data: %s", err)
            return {}
