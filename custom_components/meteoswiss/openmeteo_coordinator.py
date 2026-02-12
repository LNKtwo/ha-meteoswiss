"""Data update coordinator for Open-Meteo API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_current_weather_cache
from .const import (
    CONF_POSTAL_CODE,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_SPEED,
)

_LOGGER = logging.getLogger(__name__)

# Open-Meteo API
OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Weather condition codes (WMO)
WMO_CODES = {
    0: {"condition": "clear", "description": "Clear sky"},
    1: {"condition": "mainly_clear", "description": "Mainly clear"},
    2: {"condition": "partly_cloudy", "description": "Partly cloudy"},
    3: {"condition": "overcast", "description": "Overcast"},
    45: {"condition": "fog", "description": "Fog"},
    48: {"condition": "fog", "description": "Depositing rime fog"},
    51: {"condition": "light_rain", "description": "Light drizzle"},
    53: {"condition": "light_rain", "description": "Moderate drizzle"},
    55: {"condition": "light_rain", "description": "Dense drizzle"},
    56: {"condition": "light_rain", "description": "Light freezing drizzle"},
    57: {"condition": "light_rain", "description": "Dense freezing drizzle"},
    61: {"condition": "rain", "description": "Slight rain"},
    63: {"condition": "rain", "description": "Moderate rain"},
    65: {"condition": "rain", "description": "Heavy rain"},
    66: {"condition": "rain", "description": "Light freezing rain"},
    67: {"condition": "rain", "description": "Heavy freezing rain"},
    71: {"condition": "snow", "description": "Slight snow fall"},
    73: {"condition": "snow", "description": "Moderate snow fall"},
    75: {"condition": "snow", "description": "Heavy snow fall"},
    77: {"condition": "snow", "description": "Snow grains"},
    80: {"condition": "showers", "description": "Slight rain showers"},
    81: {"condition": "showers", "description": "Moderate rain showers"},
    82: {"condition": "showers", "description": "Violent rain showers"},
    85: {"condition": "showers", "description": "Slight snow showers"},
    86: {"condition": "showers", "description": "Heavy snow showers"},
    95: {"condition": "thunderstorm", "description": "Thunderstorm"},
    96: {"condition": "thunderstorm", "description": "Thunderstorm with slight hail"},
    99: {"condition": "thunderstorm", "description": "Thunderstorm with heavy hail"},
}


class OpenMeteoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from Open-Meteo API."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        update_interval: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self._session = session
        self.weather_code = None

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
            name=f"{DOMAIN}_openmeteo",
            update_interval=timedelta(seconds=update_interval),
        )

    def get_weather_condition(self, code: int | None) -> str:
        """Get HA weather condition from WMO code."""
        if code is None:
            return "unknown"

        weather_info = WMO_CODES.get(code, {"condition": "unknown"})
        return weather_info["condition"]

    def get_weather_description(self, code: int | None) -> str:
        """Get weather description from WMO code."""
        if code is None:
            return "Unknown"

        weather_info = WMO_CODES.get(code, {"description": "Unknown"})
        return weather_info["description"]

    async def _async_fetch_data(self) -> dict[str, Any] | None:
        """Fetch data from Open-Meteo API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        # Build API URL with current weather and hourly forecast
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,weather_code",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code",
            "timezone": "Europe/Zurich",
        }

        try:
            _LOGGER.info(
                "Fetching Open-Meteo data for lat=%s, lon=%s",
                self.latitude,
                self.longitude,
            )

            async with self._session.get(OPENMETEO_BASE_URL, params=params) as response:
                if response.status != 200:
                    _LOGGER.error("Open-Meteo API error: %s", response.status)
                    return None

                data = await response.json()
                _LOGGER.debug("Open-Meteo response: %s", data)

                return self._parse_response(data)

        except aiohttp.ClientError as err:
            _LOGGER.error("Open-Meteo API request failed: %s", err)
            return None
        except Exception as err:
            _LOGGER.error("Error fetching Open-Meteo data: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            return None

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse Open-Meteo API response."""
        try:
            result = {
                SENSOR_TEMPERATURE: None,
                SENSOR_HUMIDITY: None,
                SENSOR_WIND_SPEED: None,
                SENSOR_WIND_DIRECTION: None,
                SENSOR_PRECIPITATION: None,
                SENSOR_PRESSURE: None,
                "weather_code": None,
                "weather_condition": None,
                "weather_description": None,
                "last_update": None,
                "hourly_forecast": [],
            }

            # Parse current weather
            current = data.get("current", {})

            # Temperature
            temp = current.get("temperature_2m")
            if temp is not None:
                result[SENSOR_TEMPERATURE] = float(temp)
                _LOGGER.debug("Current temperature: %s °C", result[SENSOR_TEMPERATURE])

            # Humidity
            humidity = current.get("relative_humidity_2m")
            if humidity is not None:
                result[SENSOR_HUMIDITY] = float(humidity)
                _LOGGER.debug("Current humidity: %s %%", result[SENSOR_HUMIDITY])

            # Wind speed
            wind_speed = current.get("wind_speed_10m")
            if wind_speed is not None:
                result[SENSOR_WIND_SPEED] = float(wind_speed)
                _LOGGER.debug("Current wind speed: %s km/h", result[SENSOR_WIND_SPEED])

            # Wind direction
            wind_dir = current.get("wind_direction_10m")
            if wind_dir is not None:
                result[SENSOR_WIND_DIRECTION] = int(wind_dir)
                _LOGGER.debug("Current wind direction: %s °", result[SENSOR_WIND_DIRECTION])

            # Pressure
            pressure = current.get("pressure_msl")
            if pressure is not None:
                result[SENSOR_PRESSURE] = float(pressure)
                _LOGGER.debug("Current pressure: %s hPa", result[SENSOR_PRESSURE])

            # Weather code
            self.weather_code = current.get("weather_code")
            result["weather_code"] = self.weather_code
            result["weather_condition"] = self.get_weather_condition(self.weather_code)
            result["weather_description"] = self.get_weather_description(self.weather_code)
            _LOGGER.debug("Weather code: %s (%s: %s)",
                         self.weather_code,
                         result["weather_condition"],
                         result["weather_description"])

            # Timestamp
            time = current.get("time")
            if time:
                result["last_update"] = time
                _LOGGER.debug("Last update: %s", time)

            # Parse hourly forecast (up to 24 hours)
            hourly = data.get("hourly", {})
            hourly_time = hourly.get("time", [])
            hourly_temp = hourly.get("temperature_2m", [])
            hourly_humidity = hourly.get("relative_humidity_2m", [])
            hourly_precip = hourly.get("precipitation_probability", [])
            hourly_code = hourly.get("weather_code", [])

            # Find current hour index
            current_hour_index = 0
            for i, t in enumerate(hourly_time):
                if time and t.startswith(time[:13]):  # Match hour
                    current_hour_index = i
                    break

            # Build hourly forecast (next 24 hours)
            forecast_hours = min(24, len(hourly_time) - current_hour_index)
            for i in range(forecast_hours):
                idx = current_hour_index + i
                forecast = {
                    "datetime": hourly_time[idx],
                    "temperature": hourly_temp[idx] if idx < len(hourly_temp) else None,
                    "humidity": hourly_humidity[idx] if idx < len(hourly_humidity) else None,
                    "precipitation_probability": hourly_precip[idx] if idx < len(hourly_precip) else None,
                    "weather_code": hourly_code[idx] if idx < len(hourly_code) else None,
                    "condition": self.get_weather_condition(hourly_code[idx] if idx < len(hourly_code) else None),
                }
                result["hourly_forecast"].append(forecast)

            _LOGGER.debug("Parsed %d hours of forecast", len(result["hourly_forecast"]))

            return result

        except Exception as err:
            _LOGGER.error("Error parsing Open-Meteo response: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            return {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with caching."""
        _LOGGER.info("Fetching Open-Meteo data")

        # Get cache
        cache = get_current_weather_cache()
        cache_key = f"openmeteo:{self.latitude},{self.longitude}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            _LOGGER.info("Using cached Open-Meteo data")
            return cached_data

        data = await self._async_fetch_data()

        if data is None or not data:
            raise UpdateFailed("Failed to fetch Open-Meteo data")

        # Cache the result
        cache.set(cache_key, data)

        _LOGGER.info("Successfully updated Open-Meteo data")
        return data

    async def async_close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
