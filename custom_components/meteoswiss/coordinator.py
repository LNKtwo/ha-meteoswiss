"""Data update coordinator for MeteoSwiss."""
from __future__ import annotations

import asyncio
import csv
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE,
    CONF_POSTAL_CODE,
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

# MeteoSwiss CSV parameter IDs
PARAM_TEMPERATURE = "tre200s0"  # Temperatur 2m, 10min
PARAM_HUMIDITY = "ure200s0"  # Luftfeuchtigkeit 2m, 10min
PARAM_WIND_SPEED = "fu3010z0"  # Windgeschwindigkeit, 10min
PARAM_WIND_DIR = "dkl010z0"  # Windrichtung, 10min
PARAM_PRESSURE = "prestas0"  # Luftdruck (Station)


class MeteoSwissDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from MeteoSwiss API."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        update_interval: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.station_id = station_id.lower()  # STAC API uses lowercase
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
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_get_station_data_url(self) -> str | None:
        """Fetch the 10-minute CSV URL for the station."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch station info: %s", response.status)
                    return None

                data = await response.json()

                # Find the t_recent.csv asset
                assets = data.get("assets", {})
                asset_key = f"ogd-smn_{self.station_id}_t_recent.csv"

                if asset_key in assets:
                    return assets[asset_key].get("href")

                _LOGGER.warning("No t_recent.csv found for station %s", self.station_id)
                return None

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching station info")
            return None
        except Exception as err:
            _LOGGER.error("Error fetching station info: %s", err)
            return None

    async def _async_download_and_parse_csv(self, csv_url: str) -> dict[str, Any] | None:
        """Download CSV and parse the latest values."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.get(csv_url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to download CSV: %s", response.status)
                    return None

                content = await response.text()

            # Parse CSV (semicolon-separated)
            lines = content.strip().split("\n")

            if len(lines) < 2:
                _LOGGER.error("CSV has no data lines")
                return None

            # Parse header
            reader = csv.DictReader(lines, delimiter=";")
            rows = list(reader)

            if not rows:
                _LOGGER.error("CSV parsed to empty list")
                return None

            # Get the most recent row (last one)
            latest = rows[-1]

            return self._parse_csv_row(latest)

        except Exception as err:
            _LOGGER.error("Error parsing CSV: %s", err)
            return None

    def _parse_csv_row(self, row: dict[str, str]) -> dict[str, Any]:
        """Parse a CSV row into normalized data."""
        try:
            result = {
                SENSOR_TEMPERATURE: None,
                SENSOR_HUMIDITY: None,
                SENSOR_WIND_SPEED: None,
                SENSOR_WIND_DIRECTION: None,
                SENSOR_PRECIPITATION: None,
                SENSOR_PRESSURE: None,
                "last_update": None,
            }

            # Parse temperature (in °C)
            if PARAM_TEMPERATURE in row and row[PARAM_TEMPERATURE]:
                try:
                    result[SENSOR_TEMPERATURE] = float(row[PARAM_TEMPERATURE])
                except ValueError:
                    pass

            # Parse humidity (in %)
            if PARAM_HUMIDITY in row and row[PARAM_HUMIDITY]:
                try:
                    result[SENSOR_HUMIDITY] = float(row[PARAM_HUMIDITY])
                except ValueError:
                    pass

            # Parse wind speed (in km/h)
            if PARAM_WIND_SPEED in row and row[PARAM_WIND_SPEED]:
                try:
                    result[SENSOR_WIND_SPEED] = float(row[PARAM_WIND_SPEED])
                except ValueError:
                    pass

            # Parse wind direction (in degrees)
            if PARAM_WIND_DIR in row and row[PARAM_WIND_DIR]:
                try:
                    result[SENSOR_WIND_DIRECTION] = int(float(row[PARAM_WIND_DIR]))
                except ValueError:
                    pass

            # Parse pressure (in hPa)
            if PARAM_PRESSURE in row and row[PARAM_PRESSURE]:
                try:
                    result[SENSOR_PRESSURE] = float(row[PARAM_PRESSURE])
                except ValueError:
                    pass

            # Parse timestamp
            if "reference_timestamp" in row and row["reference_timestamp"]:
                try:
                    # Parse German date format: "01.01.2025 00:00"
                    timestamp_str = row["reference_timestamp"]
                    # Convert to ISO format
                    dt = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M")
                    result["last_update"] = dt.isoformat()
                except ValueError:
                    result["last_update"] = datetime.now().isoformat()

            return result

        except Exception as err:
            _LOGGER.error("Error parsing CSV row: %s", err)
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        _LOGGER.debug("Fetching data for station %s", self.station_id)

        # Get CSV URL
        csv_url = await self._async_get_station_data_url()

        if csv_url is None:
            raise UpdateFailed("Could not find station data URL")

        # Download and parse CSV
        parsed_data = await self._async_download_and_parse_csv(csv_url)

        if parsed_data is None or not parsed_data:
            raise UpdateFailed("Failed to parse station data")

        self._last_update = datetime.now()
        _LOGGER.debug("Successfully updated data for station %s", self.station_id)

        return parsed_data

    async def async_close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
