"""Forecast coordinator using Open-Meteo API."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_forecast_cache
from .const import WMO_WEATHER_CODES

_LOGGER = logging.getLogger(__name__)

# Open-Meteo API
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


class MeteoSwissForecastCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Class to manage fetching forecast data from Open-Meteo API."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        post_code: str | None = None,
        update_interval: int = 3600,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self._station_id = station_id.lower() if station_id else None
        self._latitude = latitude
        self._longitude = longitude
        self._post_code = post_code
        self._session = session

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until: datetime | None = None

        if latitude is None or longitude is None:
            _LOGGER.warning(
                "No coordinates provided for Open-Meteo forecast. "
                "Forecast will not be available."
            )

        super().__init__(
            hass,
            _LOGGER,
            name="meteoswiss_forecast",
            update_interval=timedelta(seconds=update_interval),
        )

    def _map_open_meteo_condition(self, weather_code: int | None, is_night: bool = False) -> str:
        """Map Open-Meteo weather code to HA condition."""
        if weather_code is None:
            return "partlycloudy"

        condition = WMO_WEATHER_CODES.get(weather_code, "partlycloudy")
        if condition == "sunny" and is_night:
            return "clear-night"
        return condition

    async def _fetch_open_meteo_forecast(self) -> list[dict[str, Any]]:
        """Fetch forecast from Open-Meteo API with retries."""
        if self._latitude is None or self._longitude is None:
            raise UpdateFailed("No coordinates available for Open-Meteo")

        if self._session is None:
            raise RuntimeError("No session provided")

        url = (
            f"{OPEN_METEO_BASE_URL}"
            f"?latitude={self._latitude}"
            f"&longitude={self._longitude}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,windspeed_10m,winddirection_10m,weather_code"
            f"&forecast_days=5"
            f"&timezone=Europe/Zurich"
        )

        _LOGGER.debug("Fetching from Open-Meteo: %s", url)

        # Retry logic with timeout
        max_retries = 3
        timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds timeout

        for attempt in range(max_retries):
            try:
                async with self._session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        if attempt < max_retries - 1:
                            _LOGGER.warning("Open-Meteo returned %s, retry %d/%d", response.status, attempt + 1, max_retries)
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        raise UpdateFailed(f"Open-Meteo API returned {response.status}")

                    data = await response.json()

            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    _LOGGER.warning("Open-Meteo timeout, retry %d/%d", attempt + 1, max_retries)
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise UpdateFailed("Open-Meteo API timeout after retries")

            except aiohttp.ClientError as err:
                if attempt < max_retries - 1:
                    _LOGGER.warning("Open-Meteo client error %s, retry %d/%d", err, attempt + 1, max_retries)
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise UpdateFailed(f"Open-Meteo API client error: {err}")

            # Success - break retry loop
            break

        forecast_data = []
        hourly = data.get("hourly", {})

        if not hourly:
            raise UpdateFailed("Open-Meteo API returned no hourly data")

        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        precip_prob = hourly.get("precipitation_probability", [])
        precip = hourly.get("precipitation", [])
        wind_speed = hourly.get("windspeed_10m", [])
        wind_dir = hourly.get("winddirection_10m", [])
        weather_codes = hourly.get("weather_code", [])

        # Build forecast list (5 days = 120 hours for daily forecast)
        # Determine day/night for each hour based on time
        for i in range(min(120, len(times))):
            weather_code = weather_codes[i] if i < len(weather_codes) else None
            
            # Check if this hour is nighttime
            time_str = times[i] if i < len(times) else ""
            is_night = False
            if time_str:
                try:
                    hour = int(time_str.split("T")[1].split(":")[0])
                    is_night = hour >= 20 or hour < 6
                except (IndexError, ValueError):
                    pass
            
            entry = {
                "datetime": times[i],
                "temperature": temps[i] if i < len(temps) else None,
                "humidity": humidity[i] if i < len(humidity) else None,
                "precipitation_probability": precip_prob[i] if i < len(precip_prob) else None,
                "precipitation": precip[i] if i < len(precip) else None,
                "wind_speed": wind_speed[i] if i < len(wind_speed) else None,
                "wind_direction": wind_dir[i] if i < len(wind_dir) else None,
                "condition": self._map_open_meteo_condition(weather_code, is_night=is_night),
            }
            forecast_data.append(entry)

        _LOGGER.debug("Fetched %d hours of forecast from Open-Meteo", len(forecast_data))
        return forecast_data

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch forecast data from Open-Meteo API with caching."""
        # Circuit breaker check
        if self._circuit_open_until and datetime.now(timezone.utc) < self._circuit_open_until:
            raise UpdateFailed("Circuit breaker open — API temporarily unavailable")

        _LOGGER.debug("Fetching forecast from Open-Meteo API")

        # Get cache
        cache = get_forecast_cache()
        cache_key = f"forecast:{self._latitude},{self._longitude}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            _LOGGER.debug("Using cached forecast data")
            return cached_data

        try:
            data = await self._fetch_open_meteo_forecast()

            # Cache the result
            cache.set(cache_key, data)

            # Circuit breaker: reset on success
            self._consecutive_failures = 0
            self._circuit_open_until = None

            _LOGGER.debug("Successfully updated forecast from Open-Meteo")
            return data
        except (aiohttp.ClientError, Exception) as err:
            _LOGGER.error("Error fetching Open-Meteo forecast: %s", err)
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = datetime.now(timezone.utc) + timedelta(minutes=5)
                _LOGGER.warning(
                    "Circuit breaker opened after %d consecutive failures",
                    self._consecutive_failures,
                )
            raise UpdateFailed(f"Failed to fetch Open-Meteo forecast: {err}")

    @property
    def data_source(self) -> str:
        """Return which API was used to fetch data."""
        return "open-meteo"

    async def async_close(self) -> None:
        """Close is handled centrally by the integration setup."""
        # Session is shared and closed in async_unload_entry
        pass
