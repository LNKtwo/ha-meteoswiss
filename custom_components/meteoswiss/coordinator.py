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

from .cache import get_current_weather_cache
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

def _create_ssl_connector() -> TCPConnector:
    """Create a new SSL connector for each session to avoid reuse issues."""
    return TCPConnector(ssl=False)

# MeteoSwiss CSV parameter IDs
# NOTE: These IDs changed in 2025! Old IDs (tre200s0, ure200s0, etc.) no longer work.
PARAM_TEMPERATURE = "tre005s0"  # Temperatur 2m, 5min average (was tre200s0)
PARAM_HUMIDITY = "xchills0"    # Luftfeuchtigkeit (was ure200s0)
PARAM_WIND_SPEED = "tde200s0"    # Windgeschwindigkeit (was fu3010z0)
PARAM_WIND_DIR = "prestas0"    # Windrichtung (was dkl010z0)
PARAM_PRESSURE = "pp0qffs0"    # Luftdruck (was prestas0)


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
            self._session = aiohttp.ClientSession(connector=_create_ssl_connector())

        try:
            url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
            _LOGGER.debug("Fetching station info from: %s", url)
            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch station info: %s", response.status)
                    return None

                data = await response.json()

                # Find the t_now.csv asset (most recent 10-min data)
                assets = data.get("assets", {})
                asset_key = f"ogd-smn_{self.station_id}_t_now.csv"

                if asset_key in assets:
                    csv_url = assets[asset_key].get("href")
                    _LOGGER.info("Found CSV URL: %s", csv_url)
                    return csv_url

                # Fallback to t_recent.csv if t_now.csv not available
                asset_key = f"ogd-smn_{self.station_id}_t_recent.csv"
                if asset_key in assets:
                    csv_url = assets[asset_key].get("href")
                    _LOGGER.info("Found CSV URL (fallback): %s", csv_url)
                    return csv_url

                _LOGGER.warning("No t_now.csv or t_recent.csv found for station %s", self.station_id)
                return None

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching station info")
            return None
        except Exception as err:
            _LOGGER.error("Error fetching station info: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            return None

    async def _async_download_and_parse_csv(self, csv_url: str) -> dict[str, Any] | None:
        """Download CSV and parse the latest values."""
        if self._session is None:
            # Use SSL disabled connector for systems with outdated certificates
            self._session = aiohttp.ClientSession(connector=_create_ssl_connector())

        try:
            _LOGGER.debug("Downloading CSV from: %s", csv_url)
            async with self._session.get(csv_url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to download CSV: %s", response.status)
                    return None

                content = await response.text()

            _LOGGER.debug("CSV content length: %d chars", len(content))

            # Parse CSV (semicolon-separated) manually
            lines = content.strip().split("\n")

            if len(lines) < 2:
                _LOGGER.error("CSV has no data lines (found %d lines)", len(lines))
                return None

            # Get header line
            header_line = lines[0]
            headers = [h.strip() for h in header_line.split(";")]

            _LOGGER.debug("CSV headers: %s", headers)

            # Get the most recent data row (last non-empty line)
            data_row = None
            for line in reversed(lines[1:]):
                if line.strip():
                    data_row = line.strip()
                    break

            if not data_row:
                _LOGGER.error("No valid data row found")
                return None

            # Parse the data row
            values = [v.strip() for v in data_row.split(";")]

            _LOGGER.debug("CSV values: %s", values)
            _LOGGER.debug("Data row: %s", data_row[:200] if len(data_row) > 200 else data_row)

            # Create a dictionary of the row
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    row_dict[header] = values[i]

            _LOGGER.debug("Row dictionary keys: %s", list(row_dict.keys()))

            # Parse the data
            return self._parse_csv_row(row_dict)

        except Exception as err:
            _LOGGER.error("Error parsing CSV: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
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
            temp_value = row.get(PARAM_TEMPERATURE)
            if temp_value and temp_value.strip():
                try:
                    result[SENSOR_TEMPERATURE] = float(temp_value)
                    _LOGGER.debug("Parsed temperature: %s °C", result[SENSOR_TEMPERATURE])
                except (ValueError, TypeError) as e:
                    _LOGGER.error("Could not parse temperature '%s': %s", temp_value, e)

            # Parse humidity (in %)
            hum_value = row.get(PARAM_HUMIDITY)
            if hum_value and hum_value.strip():
                try:
                    result[SENSOR_HUMIDITY] = float(hum_value)
                    _LOGGER.debug("Parsed humidity: %s %%", result[SENSOR_HUMIDITY])
                except (ValueError, TypeError) as e:
                    _LOGGER.error("Could not parse humidity '%s': %s", hum_value, e)

            # Parse wind speed (in km/h)
            wind_value = row.get(PARAM_WIND_SPEED)
            if wind_value and wind_value.strip():
                try:
                    result[SENSOR_WIND_SPEED] = float(wind_value)
                    _LOGGER.debug("Parsed wind speed: %s km/h", result[SENSOR_WIND_SPEED])
                except (ValueError, TypeError) as e:
                    _LOGGER.error("Could not parse wind speed '%s': %s", wind_value, e)

            # Parse wind direction (in degrees)
            dir_value = row.get(PARAM_WIND_DIR)
            if dir_value and dir_value.strip():
                try:
                    result[SENSOR_WIND_DIRECTION] = int(float(dir_value))
                    _LOGGER.debug("Parsed wind direction: %s °", result[SENSOR_WIND_DIRECTION])
                except (ValueError, TypeError) as e:
                    _LOGGER.error("Could not parse wind direction '%s': %s", dir_value, e)

            # Parse pressure (in hPa)
            press_value = row.get(PARAM_PRESSURE)
            if press_value and press_value.strip():
                try:
                    result[SENSOR_PRESSURE] = float(press_value)
                    _LOGGER.debug("Parsed pressure: %s hPa", result[SENSOR_PRESSURE])
                except (ValueError, TypeError) as e:
                    _LOGGER.error("Could not parse pressure '%s': %s", press_value, e)

            # Parse timestamp
            timestamp_value = row.get("reference_timestamp")
            if timestamp_value and timestamp_value.strip():
                try:
                    # Parse German date format: "01.01.2025 00:00"
                    timestamp_str = timestamp_value.strip()
                    # Convert to ISO format
                    dt = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M")
                    result["last_update"] = dt.isoformat()
                    _LOGGER.debug("Parsed timestamp: %s", result["last_update"])
                except ValueError as e:
                    _LOGGER.error("Could not parse timestamp '%s': %s", timestamp_value, e)
                    result["last_update"] = datetime.now().isoformat()

            # Log final result
            _LOGGER.info("Parsed result: temp=%s, humidity=%s, wind=%s, dir=%s, pressure=%s",
                        result[SENSOR_TEMPERATURE],
                        result[SENSOR_HUMIDITY],
                        result[SENSOR_WIND_SPEED],
                        result[SENSOR_WIND_DIRECTION],
                        result[SENSOR_PRESSURE])

            return result

        except Exception as err:
            _LOGGER.error("Error parsing CSV row: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with caching."""
        _LOGGER.info("=== FETCHING DATA FOR STATION %s ===", self.station_id)

        # Get cache
        cache = get_current_weather_cache()
        cache_key = f"station:{self.station_id}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            _LOGGER.info("✅ Using cached data for station %s", self.station_id)
            _LOGGER.info("Cache data: %s", cached_data)
            return cached_data

        _LOGGER.info("❌ Cache miss, fetching fresh data for station %s", self.station_id)

        # Get CSV URL
        csv_url = await self._async_get_station_data_url()

        if csv_url is None:
            _LOGGER.error("Failed to find station data URL")
            raise UpdateFailed("Could not find station data URL")

        _LOGGER.info("Fetching CSV from: %s", csv_url)

        # Download and parse CSV
        parsed_data = await self._async_download_and_parse_csv(csv_url)

        if parsed_data is None:
            _LOGGER.error("Parsed data is None!")
            raise UpdateFailed("Failed to parse station data: parsed_data is None")

        if not parsed_data:
            _LOGGER.error("Parsed data is empty!")
            raise UpdateFailed("Failed to parse station data: parsed_data is empty")

        _LOGGER.info("✅ Successfully parsed data: %s", parsed_data)

        self._last_update = datetime.now()

        # Cache the result
        cache.set(cache_key, parsed_data)
        _LOGGER.info("✅ Cached data for station %s (TTL: 300s)", self.station_id)

        _LOGGER.info("=== FETCH COMPLETE FOR STATION %s ===", self.station_id)

        return parsed_data

    async def async_close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
