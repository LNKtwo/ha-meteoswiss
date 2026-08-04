"""Data update coordinator for MeteoSwiss."""
from __future__ import annotations

import asyncio
import csv
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_current_weather_cache
from .const import (
    API_BASE,
    CONF_POSTAL_CODE,
    DOMAIN,
    GRANULARITY_10MIN,
    MIN_UPDATE_INTERVAL,
    SENSOR_DEW_POINT,
    SENSOR_FOEHN_INDEX,
    SENSOR_GLOBAL_RADIATION,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_SNOW_DEPTH,
    SENSOR_SOIL_TEMP_10CM,
    SENSOR_SOIL_TEMP_20CM,
    SENSOR_SOIL_TEMP_5CM,
    SENSOR_SUNSHINE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_GUST,
    SENSOR_WIND_SPEED,
    STAC_COLLECTION,
)
from .retry import async_retry_with_backoff

_LOGGER = logging.getLogger(__name__)

# MeteoSwiss CSV parameter IDs (10-minute granularity)
# These are the column headers in the CSV files from data.geo.admin.ch
PARAM_TEMPERATURE = "tre200s0"  # Lufttemperatur 2m über Boden; Momentanwert (°C)
PARAM_HUMIDITY = "ure200s0"    # Relative Luftfeuchtigkeit 2m über Boden (%)
PARAM_WIND_SPEED = "fu3010z0"  # Windgeschwindigkeit; Zehnminutenmittel (km/h)
PARAM_WIND_DIR = "dkl010z0"    # Windrichtung; Zehnminutenmittel (°)
PARAM_PRESSURE = "pp0qffs0"    # Luftdruck reduziert auf Meeresniveau QFF (hPa)
PARAM_PRECIPITATION = "rre150z0"  # Niederschlag; Zehnminutensumme (mm)
PARAM_GUST_1S = "fu3010z1"     # Böenspitze (Sekundenböe); Maximum (km/h)
PARAM_GUST_3S = "fu3010z3"     # Böenspitze (3-Sekundenböe); Maximum (km/h)
PARAM_SUNSHINE = "sre000z0"    # Sonnenscheindauer; Zehnminutensumme (min)
PARAM_GLOBAL_RAD = "gre000z0"  # Globalstrahlung; Zehnminutenmittel (W/m²)
PARAM_SNOW_DEPTH = "htoauts0"  # Gesamtschneehöhe; Momentanwert (cm)
PARAM_DEW_POINT = "tde200s0"  # Taupunkt 2m über Boden; Momentanwert (°C)
PARAM_FOEHN_INDEX = "wcc006s0"  # Föhnindex; Momentanwert (Code)
PARAM_SOIL_TEMP_5CM = "tso005s0"  # Bodentemperatur 5 cm Tiefe; Momentanwert (°C)
PARAM_SOIL_TEMP_10CM = "tso010s0"  # Bodentemperatur 10 cm Tiefe; Momentanwert (°C)
PARAM_SOIL_TEMP_20CM = "tso020s0"  # Bodentemperatur 20 cm Tiefe; Momentanwert (°C)


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

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until: datetime | None = None

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

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_get_station_data_url(self) -> str | None:
        """Fetch the 10-minute CSV URL for the station."""
        if self._session is None:
            raise RuntimeError("No session provided")

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
                    _LOGGER.debug("Found CSV URL: %s", csv_url)
                    return csv_url

                # Fallback to t_recent.csv if t_now.csv not available
                asset_key = f"ogd-smn_{self.station_id}_t_recent.csv"
                if asset_key in assets:
                    csv_url = assets[asset_key].get("href")
                    _LOGGER.debug("Found CSV URL (fallback): %s", csv_url)
                    return csv_url

                _LOGGER.warning("No t_now.csv or t_recent.csv found for station %s", self.station_id)
                return None

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching station info")
            return None
        except Exception as err:
            _LOGGER.exception("Error fetching station info: %s", err)
            return None

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_download_and_parse_csv(self, csv_url: str) -> dict[str, Any] | None:
        """Download CSV and parse the latest values."""
        if self._session is None:
            raise RuntimeError("No session provided")

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

            # Collect recent data rows (last 5 non-empty lines) for fallback parsing
            recent_rows: list[str] = []
            for line in reversed(lines[1:]):
                if line.strip():
                    recent_rows.append(line.strip())
                    if len(recent_rows) >= 5:
                        break

            if not recent_rows:
                _LOGGER.error("No valid data row found")
                return None

            # Parse rows into dicts (newest first)
            row_dicts: list[dict[str, str]] = []
            for data_row in recent_rows:
                values = [v.strip() for v in data_row.split(";")]
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(values):
                        row_dict[header] = values[i]
                row_dicts.append(row_dict)

            _LOGGER.debug("CSV recent rows: %d", len(row_dicts))

            # Parse the data using newest row, with fallback for empty values
            return self._parse_csv_row_with_fallback(row_dicts)

        except Exception as err:
            _LOGGER.exception("Error parsing CSV: %s", err)
            return None

    def _parse_csv_row_with_fallback(self, row_dicts: list[dict[str, str]]) -> dict[str, Any]:
        """Parse CSV rows into normalized data, using fallback for empty values."""
        if not row_dicts:
            return {}
        # Parse newest row first, then fill missing values from older rows
        result = self._parse_csv_row(row_dicts[0])
        
        # Parameters that might be empty in newest row but available in older rows
        fallback_params = [
            PARAM_FOEHN_INDEX,
            PARAM_SOIL_TEMP_5CM,
            PARAM_SOIL_TEMP_10CM,
            PARAM_SOIL_TEMP_20CM,
            PARAM_SNOW_DEPTH,
        ]
        param_to_sensor = {
            PARAM_FOEHN_INDEX: SENSOR_FOEHN_INDEX,
            PARAM_SOIL_TEMP_5CM: SENSOR_SOIL_TEMP_5CM,
            PARAM_SOIL_TEMP_10CM: SENSOR_SOIL_TEMP_10CM,
            PARAM_SOIL_TEMP_20CM: SENSOR_SOIL_TEMP_20CM,
            PARAM_SNOW_DEPTH: SENSOR_SNOW_DEPTH,
        }
        
        for param_key in fallback_params:
            sensor_key = param_to_sensor[param_key]
            if result.get(sensor_key) is None:
                for older_row in row_dicts[1:]:
                    val = older_row.get(param_key, "").strip()
                    if val:
                        try:
                            if sensor_key == SENSOR_FOEHN_INDEX:
                                result[sensor_key] = int(float(val))
                            else:
                                result[sensor_key] = float(val)
                            _LOGGER.debug("Fallback %s from older row: %s", sensor_key, result[sensor_key])
                            break
                        except (ValueError, TypeError):
                            pass
        
        return result

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
                SENSOR_WIND_GUST: None,
                SENSOR_DEW_POINT: None,
                SENSOR_SUNSHINE: None,
                SENSOR_GLOBAL_RADIATION: None,
                SENSOR_SNOW_DEPTH: None,
                SENSOR_FOEHN_INDEX: None,
                SENSOR_SOIL_TEMP_5CM: None,
                SENSOR_SOIL_TEMP_10CM: None,
                SENSOR_SOIL_TEMP_20CM: None,
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

            # Parse precipitation (in mm)
            precip_value = row.get(PARAM_PRECIPITATION)
            if precip_value and precip_value.strip():
                try:
                    result[SENSOR_PRECIPITATION] = float(precip_value)
                    _LOGGER.debug("Parsed precipitation: %s mm", result[SENSOR_PRECIPITATION])
                except (ValueError, TypeError) as e:
                    _LOGGER.error("Could not parse precipitation '%s': %s", precip_value, e)

            # Parse wind gust (1-second, in km/h)
            gust_value = row.get(PARAM_GUST_1S)
            if gust_value and gust_value.strip():
                try:
                    result[SENSOR_WIND_GUST] = float(gust_value)
                except (ValueError, TypeError) as e:
                    _LOGGER.debug("Could not parse wind gust '%s': %s", gust_value, e)

            # Parse sunshine duration (10-min sum, in minutes)
            sun_value = row.get(PARAM_SUNSHINE)
            if sun_value and sun_value.strip():
                try:
                    result[SENSOR_SUNSHINE] = float(sun_value)
                except (ValueError, TypeError) as e:
                    _LOGGER.debug("Could not parse sunshine '%s': %s", sun_value, e)

            # Parse global radiation (W/m²)
            rad_value = row.get(PARAM_GLOBAL_RAD)
            if rad_value and rad_value.strip():
                try:
                    result[SENSOR_GLOBAL_RADIATION] = float(rad_value)
                except (ValueError, TypeError) as e:
                    _LOGGER.debug("Could not parse global radiation '%s': %s", rad_value, e)

            # Parse snow depth (cm)
            snow_value = row.get(PARAM_SNOW_DEPTH)
            if snow_value and snow_value.strip():
                try:
                    result[SENSOR_SNOW_DEPTH] = float(snow_value)
                    _LOGGER.debug("Parsed snow depth: %s cm", result[SENSOR_SNOW_DEPTH])
                except (ValueError, TypeError) as e:
                    _LOGGER.debug("Could not parse snow depth '%s': %s", snow_value, e)

            # Parse foehn index (code)
            foehn_value = row.get(PARAM_FOEHN_INDEX)
            if foehn_value and foehn_value.strip():
                try:
                    result[SENSOR_FOEHN_INDEX] = int(float(foehn_value))
                    _LOGGER.debug("Parsed foehn index: %s", result[SENSOR_FOEHN_INDEX])
                except (ValueError, TypeError) as e:
                    _LOGGER.debug("Could not parse foehn index '%s': %s", foehn_value, e)

            # Parse soil temperatures (°C)
            for param_key, sensor_key in (
                (PARAM_SOIL_TEMP_5CM, SENSOR_SOIL_TEMP_5CM),
                (PARAM_SOIL_TEMP_10CM, SENSOR_SOIL_TEMP_10CM),
                (PARAM_SOIL_TEMP_20CM, SENSOR_SOIL_TEMP_20CM),
            ):
                soil_value = row.get(param_key)
                if soil_value and soil_value.strip():
                    try:
                        result[sensor_key] = float(soil_value)
                        _LOGGER.debug("Parsed %s: %s °C", sensor_key, result[sensor_key])
                    except (ValueError, TypeError) as e:
                        _LOGGER.debug("Could not parse %s '%s': %s", sensor_key, soil_value, e)

            # Dew point: use measured value if available, otherwise calculate via Magnus formula
            dew_measured = row.get(PARAM_DEW_POINT)
            if dew_measured and dew_measured.strip():
                try:
                    result[SENSOR_DEW_POINT] = round(float(dew_measured), 1)
                    _LOGGER.debug("Using measured dew point: %s °C", result[SENSOR_DEW_POINT])
                except (ValueError, TypeError) as e:
                    _LOGGER.debug("Could not parse measured dew point '%s': %s", dew_measured, e)

            # Fallback: calculate dew point from temperature and humidity using Magnus formula
            if result[SENSOR_DEW_POINT] is None:
                temp = result.get(SENSOR_TEMPERATURE)
                hum = result.get(SENSOR_HUMIDITY)
                if temp is not None and hum is not None:
                    try:
                        # Magnus formula
                        a = 17.625
                        b = 243.04
                        alpha = ((a * temp) / (b + temp)) + math.log(max(hum, 1.0) / 100.0)
                        dew = (b * alpha) / (a - alpha)
                        result[SENSOR_DEW_POINT] = round(dew, 1)
                        _LOGGER.debug("Calculated dew point (Magnus): %s °C", result[SENSOR_DEW_POINT])
                    except Exception:
                        pass

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
            _LOGGER.debug("Parsed result: temp=%s, humidity=%s, wind=%s, dir=%s, pressure=%s",
                        result[SENSOR_TEMPERATURE],
                        result[SENSOR_HUMIDITY],
                        result[SENSOR_WIND_SPEED],
                        result[SENSOR_WIND_DIRECTION],
                        result[SENSOR_PRESSURE])

            return result

        except Exception as err:
            _LOGGER.exception("Error parsing CSV row: %s", err)
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with caching."""
        # Circuit breaker check
        if self._circuit_open_until and datetime.now(timezone.utc) < self._circuit_open_until:
            raise UpdateFailed("Circuit breaker open — API temporarily unavailable")

        try:
            _LOGGER.debug("Fetching data for station %s", self.station_id)

            # Get cache
            cache = get_current_weather_cache()
            cache_key = f"station:{self.station_id}"

            # Try cache first
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                _LOGGER.debug("Using cached data for station %s", self.station_id)
                return cached_data

            _LOGGER.debug("Cache miss, fetching fresh data for station %s", self.station_id)

            # Get CSV URL
            csv_url = await self._async_get_station_data_url()

            if csv_url is None:
                _LOGGER.error("Failed to find station data URL")
                raise UpdateFailed("Could not find station data URL")

            _LOGGER.debug("Fetching CSV from: %s", csv_url)

            # Download and parse CSV
            parsed_data = await self._async_download_and_parse_csv(csv_url)

            if parsed_data is None:
                _LOGGER.error("Parsed data is None!")
                raise UpdateFailed("Failed to parse station data: parsed_data is None")

            if not parsed_data:
                _LOGGER.error("Parsed data is empty!")
                raise UpdateFailed("Failed to parse station data: parsed_data is empty")

            _LOGGER.debug("Successfully parsed data: %s", parsed_data)

            self._last_update = datetime.now()

            # Circuit breaker: reset on success
            self._consecutive_failures = 0
            self._circuit_open_until = None

            # Cache result
            cache.set(cache_key, parsed_data)
            _LOGGER.debug("Cached data for station %s (TTL: 600s)", self.station_id)

            return parsed_data

        except UpdateFailed:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = datetime.now(timezone.utc) + timedelta(minutes=5)
                _LOGGER.warning(
                    "Circuit breaker opened after %d consecutive failures",
                    self._consecutive_failures,
                )
            raise

    async def async_close(self) -> None:
        """Close is handled centrally by the integration setup."""
        # Session is shared and closed in async_unload_entry
        pass
