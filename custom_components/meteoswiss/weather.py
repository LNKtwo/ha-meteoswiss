"""Weather platform for meteoswiss integration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Final

from homeassistant.components.weather import WeatherEntity, Forecast
from homeassistant.const import UnitOfPressure, UnitOfPrecipitationDepth, UnitOfSpeed, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION_NAME,
    DOMAIN,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_SPEED,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .forecast_coordinator import MeteoSwissForecastCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up weather platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    forecast_coordinator = hass.data[DOMAIN][entry.entry_id].get("forecast_coordinator")
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    entity = MeteoSwissWeather(coordinator, forecast_coordinator, entry, station_name)

    # Listen for forecast coordinator updates
    if forecast_coordinator:
        forecast_coordinator.async_add_listener(entity._handle_forecast_update)
        _LOGGER.info("Subscribed to forecast coordinator updates")

    async_add_entities([entity])


class MeteoSwissWeather(CoordinatorEntity[MeteoSwissDataUpdateCoordinator], WeatherEntity):
    """Representation of meteoswiss weather data."""

    # WMO weather code mapping for Open-Meteo
    # https://open-meteo.com/en/docs
    WEATHER_CODE_MAP: Final[dict[int, str]] = {
        0: "clear-night",
        1: "sunny",
        2: "partlycloudy",
        3: "partlycloudy",
        45: "fog",
        48: "fog",
        51: "rainy",
        53: "rainy",
        55: "rainy",
        56: "rainy",
        57: "rainy",
        61: "rainy",
        63: "rainy",
        65: "rainy",
        66: "rainy",
        67: "rainy",
        71: "snowy",
        73: "snowy",
        75: "snowy",
        77: "snowy",
        77: "snowy",
        80: "rainy",
        81: "rainy",
        82: "rainy",
        85: "snowy",
        86: "snowy",
        95: "lightning",
        96: "lightning",
        99: "lightning",
    }

    # MeteoSwiss symbol/condition mapping (if available)
    METEOSWISS_CONDITION_MAP: Final[dict[str, str]] = {
        "clear": "sunny",
        "sunny": "sunny",
        "partly-cloudy": "partlycloudy",
        "cloudy": "cloudy",
        "overcast": "cloudy",
        "rain": "rainy",
        "rainy": "rainy",
        "snow": "snowy",
        "snowy": "snowy",
        "fog": "fog",
        "mist": "fog",
        "thunderstorm": "lightning",
    }

    def __init__(
        self,
        coordinator: MeteoSwissDataUpdateCoordinator,
        forecast_coordinator: MeteoSwissForecastCoordinator,
        entry: ConfigEntry,
        station_name: str,
    ) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
        self._forecast_coordinator = forecast_coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="SwissMetNet",
        )
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_weather"
        self._attr_attribution = ATTRIBUTION
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
        self._attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

        # Log coordinates for debug
        lat = entry.data.get(CONF_LATITUDE)
        lon = entry.data.get(CONF_LONGITUDE)
        _LOGGER.info("WeatherEntity initialized - lat/lon: %s/%s", lat, lon)

    @property
    def coordinator_data(self) -> dict:
        """Return coordinator data."""
        if not self.coordinator:
            _LOGGER.warning("Current weather coordinator is None!")
            return {}

        data = self.coordinator.data
        _LOGGER.debug("MeteoSwiss coordinator data: %s", data)
        return data

    @property
    def forecast_coordinator_data(self) -> list:
        """Return forecast coordinator data."""
        if not self._forecast_coordinator:
            _LOGGER.warning("Forecast coordinator is None!")
            return []

        data = self._forecast_coordinator.data
        _LOGGER.debug("Forecast coordinator data (count): %d", len(data) if data else 0)
        return data

    @callback
    def _handle_forecast_update(self) -> None:
        """Handle forecast coordinator update."""
        _LOGGER.debug("Forecast update triggered")
        self.async_write_ha_state()

    @property
    def supported_features(self) -> int:
        """Return supported features."""
        from homeassistant.components.weather import WeatherEntityFeature
        return WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    def _map_open_meteo_condition(self, weather_code: int | None) -> str | None:
        """Map Open-Meteo weather code to HA condition."""
        if weather_code is None:
            _LOGGER.debug("Open-Meteo weather_code is None")
            return None

        condition = self.WEATHER_CODE_MAP.get(weather_code, "partlycloudy")
        _LOGGER.debug("Mapped Open-Meteo code %s → condition: %s", weather_code, condition)
        return condition

    def _resolve_condition(self) -> str | None:
        """Resolve current condition with fallback logic.

        Priority order:
        1. Open-Meteo current weather (from forecast coordinator)
        2. MeteoSwiss symbol/icon
        3. Precipitation-based fallback
        4. Safe fallback ("partlycloudy") if numeric data exists
        5. None if absolutely no data

        Returns:
            HA condition string or None
        """
        # Log resolution start
        _LOGGER.debug("=== RESOLVING CURRENT CONDITION ===")

        # Try Open-Meteo current weather first
        forecast_data = self.forecast_coordinator_data
        if forecast_data and len(forecast_data) > 0:
            # Try to find current hour in forecast data
            now = datetime.now(timezone.utc)
            for entry in forecast_data[:6]:  # Check next 6 hours
                entry_time = entry.get("datetime")
                if entry_time:
                    try:
                        # Parse ISO datetime
                        if isinstance(entry_time, str):
                            entry_dt = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
                            # Check if this entry is within 30 minutes of now
                            if abs((entry_dt - now).total_seconds()) < 1800:  # 30 min window
                                weather_code = entry.get("weather_code")
                                condition = self._map_open_meteo_condition(weather_code)
                                if condition:
                                    _LOGGER.info("✅ Condition resolved via Open-Meteo: %s (code: %s)", condition, weather_code)
                                    return condition
                    except Exception as err:
                        _LOGGER.debug("Error parsing forecast datetime: %s", err)
                        continue

            # Fallback: use first forecast entry if no close match
            first_entry = forecast_data[0]
            weather_code = first_entry.get("weather_code")
            condition = self._map_open_meteo_condition(weather_code)
            if condition:
                _LOGGER.info("✅ Condition resolved via Open-Meteo (first entry): %s (code: %s)", condition, weather_code)
                return condition
            else:
                _LOGGER.debug("Open-Meteo forecast exists but no valid weather_code")

        else:
            _LOGGER.info("Open-Meteo current data not available")

        # Try MeteoSwiss symbol/icon
        ms_data = self.coordinator_data
        if ms_data:
            for key in ["symbol", "icon", "condition"]:
                symbol = ms_data.get(key)
                if symbol:
                    condition = self.METEOSWISS_CONDITION_MAP.get(str(symbol).lower())
                    if condition:
                        _LOGGER.info("✅ Condition resolved via MeteoSwiss symbol: %s (symbol: %s)", condition, symbol)
                        return condition
                    else:
                        _LOGGER.debug("MeteoSwiss symbol '%s' has no mapping", symbol)

        # Try precipitation-based fallback
        if ms_data:
            precip = ms_data.get(SENSOR_PRECIPITATION)
            if precip is not None:
                if precip > 0:
                    _LOGGER.info("✅ Condition resolved via precipitation fallback: rainy (%s mm)", precip)
                    return "rainy"

                # Time-based fallback (day/night)
                now_hour = datetime.now().hour
                # Swiss timezone is UTC+1, so adjust
                # Night: 21:00-07:00 Swiss = 20:00-06:00 UTC
                is_night = now_hour >= 20 or now_hour < 6
                if is_night:
                    _LOGGER.info("✅ Condition resolved via time fallback: clear-night")
                    return "clear-night"
                else:
                    _LOGGER.info("✅ Condition resolved via time fallback: partlycloudy")
                    return "partlycloudy"

        # Safe fallback if any numeric data exists
        if ms_data and (ms_data.get(SENSOR_TEMPERATURE) is not None or ms_data.get(SENSOR_HUMIDITY) is not None):
            _LOGGER.warning("⚠️ Using safe fallback condition: partlycloudy (no condition source available)")
            return "partlycloudy"

        # Absolutely no data
        _LOGGER.error("❌ No condition data available, returning None")
        return None

    @property
    def condition(self) -> str | None:
        """Return current condition with fallback logic."""
        return self._resolve_condition()

    @property
    def temperature(self) -> float | None:
        """Return temperature."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_TEMPERATURE)
        return None

    @property
    def pressure(self) -> float | None:
        """Return pressure."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_PRESSURE)
        return None

    @property
    def humidity(self) -> int | None:
        """Return humidity."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_HUMIDITY)
        return None

    @property
    def wind_speed(self) -> float | None:
        """Return wind speed."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_WIND_SPEED)
        return None

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_WIND_DIRECTION)
        return None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast."""
        _LOGGER.debug("=== HOURLY FORECAST REQUEST ===")

        forecast_data = self.forecast_coordinator_data

        if not forecast_data:
            _LOGGER.warning("No forecast data available for hourly forecast")
            return None

        _LOGGER.info("Building hourly forecast from %d entries", len(forecast_data))

        ha_forecast = []
        for entry in forecast_data[:24]:  # Limit to 24 hours
            try:
                dt = entry.get("datetime")
                temp = entry.get("temperature")

                if dt and temp is not None:
                    ha_forecast.append(Forecast(
                        datetime=dt,
                        temperature=temp,
                        precipitation=entry.get("precipitation"),
                        precipitation_probability=entry.get("precipitation_probability"),
                        wind_speed=entry.get("wind_speed"),
                        wind_bearing=entry.get("wind_direction"),
                        condition=entry.get("condition"),
                    ))
            except Exception as err:
                _LOGGER.warning("Error building hourly forecast entry: %s", err)
                continue

        _LOGGER.debug("Returning %d hourly forecast entries", len(ha_forecast))
        return ha_forecast if ha_forecast else None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast (derived from hourly)."""
        _LOGGER.debug("=== DAILY FORECAST REQUEST ===")

        forecast_data = self.forecast_coordinator_data

        if not forecast_data:
            _LOGGER.warning("No forecast data available for daily forecast")
            return None

        _LOGGER.info("Building daily forecast from %d hourly entries", len(forecast_data))

        # Group hourly data by day (up to 5 days = 120 hours)
        daily_data = {}
        for entry in forecast_data[:120]:
            try:
                dt_str = entry.get("datetime", "")
                if not dt_str:
                    continue

                date_str = dt_str[:10]  # Get date part (YYYY-MM-DD)
                if date_str not in daily_data:
                    daily_data[date_str] = []
                daily_data[date_str].append(entry)
            except Exception as err:
                _LOGGER.warning("Error processing daily forecast entry: %s", err)
                continue

        # Build daily forecast (one entry per day)
        ha_forecast = []
        for date_str, hourly_entries in list(daily_data.items())[:5]:  # Max 5 days
            try:
                if not hourly_entries:
                    continue

                # Use midday (12:00-14:00) as representative temperature
                midday_entries = [
                    e for e in hourly_entries
                    if "T12:" in e.get("datetime", "") or
                    "T13:" in e.get("datetime", "") or
                    "T14:" in e.get("datetime", "")
                ]
                representative = midday_entries[0] if midday_entries else hourly_entries[0]

                ha_forecast.append(Forecast(
                    datetime=representative.get("datetime"),
                    temperature=representative.get("temperature"),
                    precipitation=sum(e.get("precipitation", 0) for e in hourly_entries),
                    precipitation_probability=max(e.get("precipitation_probability", 0) for e in hourly_entries),
                    wind_speed=representative.get("wind_speed"),
                    wind_bearing=representative.get("wind_direction"),
                    condition=representative.get("condition"),
                ))
            except Exception as err:
                _LOGGER.warning("Error building daily forecast for %s: %s", date_str, err)
                continue

        _LOGGER.debug("Returning %d daily forecast entries", len(ha_forecast))
        return ha_forecast if ha_forecast else None

    @property
    def forecast(self) -> list | None:
        """Return forecast (deprecated, use async_forecast_hourly)."""
        # For backward compatibility
        forecast_data = self.forecast_coordinator_data
        if not forecast_data:
            return None
        ha_forecast = []
        for entry in forecast_data[:24]:
            if entry.get("datetime") and entry.get("temperature") is not None:
                ha_forecast.append({
                    "datetime": entry["datetime"],
                    "temperature": entry["temperature"],
                    "precipitation": entry.get("precipitation"),
                })
        return ha_forecast
