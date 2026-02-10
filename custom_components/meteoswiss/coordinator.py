"""Data update coordinator for MeteoSwiss."""
from __future__ import annotations

import asyncio
import csv
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from aiohttp import TCPConnector

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

# SSL connector for systems with outdated certificates
# This is a fallback for systems that cannot update CA certificates
_SSL_CONNECTOR = TCPConnector(ssl=False)

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
            # Use SSL disabled connector for systems with outdated certificates
            self._session = aiohttp.ClientSession(connector=_SSL_CONNECTOR)

        try:
            url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch station info: %s", response.status)
                    return None

                data = await response.json()

                # Find the t_now.csv asset (most recent 10-min data)
                assets = data.get("assets", {})
                asset_key = f"ogd-smn_{self.station_id}_t_now.csv"

                if asset_key in assets:
                    return assets[asset_key].get("href")

                # Fallback to t_recent.csv if t_now.csv not available
                asset_key = f"ogd-smn_{self.station_id}_t_recent.csv"
                if asset_key in assets:
                    return assets[asset_key].get("href")

                _LOGGER.warning("No t_now.csv or t_recent.csv found for station %s", self.station_id)
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
            # Use SSL disabled connector for systems with outdated certificates
            self._session = aiohttp.ClientSession(connector=_SSL_CONNECTOR)

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

            # Parse header and data rows
            reader = csv.DictReader(lines, delimiter=";")
            rows = list(reader)

            if not rows:
                _LOGGER.error("CSV parsed to empty list")
                return None

            # Get the most recent row (last one)
            latest = rows[-1]
            _LOGGER.debug("Latest CSV row: %s", latest)

            parsed = self._parse_csv_row(latest)
            _LOGGER.debug("Parsed data: %s", parsed)

            return parsed

        except Exception as err:
            _LOGGER.error("Error parsing CSV: %s", err)
            import traceback
            _LOGGER.error("Traceback: %s", traceback.format_exc())
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
            if PARAM_TEMPERATURE in row:
                temp_value = row[PARAM_TEMPERATURE]
                if temp_value and temp_value.strip():
                    try:
                        result[SENSOR_TEMPERATURE] = float(temp_value)
                    except (ValueError, TypeError):
                        _LOGGER.debug("Could not parse temperature: %s", temp_value)

            # Parse humidity (in %)
            if PARAM_HUMIDITY in row:
                hum_value = row[PARAM_HUMIDITY]
                if hum_value and hum_value.strip():
                    try:
                        result[SENSOR_HUMIDITY] = float(hum_value)
                    except (ValueError, TypeError):
                        _LOGGER.debug("Could not parse humidity: %s", hum_value)

            # Parse wind speed (in km/h)
            if PARAM_WIND_SPEED in row:
                wind_value = row[PARAM_WIND_SPEED]
                if wind_value and wind_value.strip():
                    try:
                        result[SENSOR_WIND_SPEED] = float(wind_value)
                    except (ValueError, TypeError):
                        _LOGGER.debug("Could not parse wind speed: %s", wind_value)

            # Parse wind direction (in degrees)
            if PARAM_WIND_DIR in row:
                dir_value = row[PARAM_WIND_DIR]
                if dir_value and dir_value.strip():
                    try:
                        result[SENSOR_WIND_DIRECTION] = int(float(dir_value))
                    except (ValueError, TypeError):
                        _LOGGER.debug("Could not parse wind direction: %s", dir_value)

            # Parse pressure (in hPa)
            if PARAM_PRESSURE in row:
                press_value = row[PARAM_PRESSURE]
                if press_value and press_value.strip():
                    try:
                        result[SENSOR_PRESSURE] = float(press_value)
                    except (ValueError, TypeError):
                        _LOGGER.debug("Could not parse pressure: %s", press_value)

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
