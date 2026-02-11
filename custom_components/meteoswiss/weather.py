"""Weather platform for meteoswiss integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Final

from homeassistant.components.weather import WeatherEntity, Forecast
from homeassistant.const import UnitOfPressure, UnitOfPrecipitationDepth, UnitOfSpeed, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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

    # Get coordinates from STAC data (stored in coordinator or entry data)
    lat = entry.data.get(CONF_LATITUDE)
    lon = entry.data.get(CONF_LONGITUDE)
    post_code = entry.data.get("post_code")

    forecast_coordinator = MeteoSwissForecastCoordinator(
        hass,
        station_id=entry.data.get("station_id"),
        latitude=lat,
        longitude=lon,
        post_code=post_code,
        update_interval=3600,  # Update every hour
    )
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    entity = MeteoSwissWeather(coordinator, forecast_coordinator, entry, station_name)

    async_add_entities([entity])

    # Fetch forecast data initially
    await forecast_coordinator.async_config_entry_first_refresh()


class MeteoSwissWeather(CoordinatorEntity[MeteoSwissDataUpdateCoordinator], WeatherEntity):
    """Representation of meteoswiss weather data."""

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

    @property
    def coordinator_data(self) -> dict:
        """Return coordinator data."""
        return self.coordinator.data if self.coordinator else {}

    @property
    def supported_features(self) -> int:
        """Return supported features."""
        from homeassistant.components.weather import WeatherEntityFeature
        return WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    @property
    def condition(self) -> str | None:
        """Return current condition based on precipitation and time of day."""
        if not self.coordinator_data:
            return None

        precip = self.coordinator_data.get(SENSOR_PRECIPITATION)

        # If raining
        if precip and precip > 0:
            return "rainy"

        # Determine day/night based on current hour (Swiss timezone roughly UTC+1)
        now = datetime.now().hour
        # Night: 20:00 - 06:00
        is_night = now >= 20 or now < 6

        if is_night:
            return "clear-night"
        else:
            return "sunny"

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
        forecast_data = self._forecast_coordinator.data if self._forecast_coordinator else []

        if not forecast_data:
            _LOGGER.warning("No forecast data available")
            return None

        ha_forecast = []
        for entry in forecast_data[:24]:  # Limit to 24 hours
            if entry.get("datetime") and entry.get("temperature") is not None:
                ha_forecast.append(Forecast(
                    datetime=entry["datetime"],
                    temperature=entry["temperature"],
                    precipitation=entry.get("precipitation"),
                    precipitation_probability=entry.get("precipitation_probability"),
                    wind_speed=entry.get("wind_speed"),
                    wind_bearing=entry.get("wind_direction"),
                    condition=entry.get("condition"),
                ))

        _LOGGER.debug("Returning %d hourly forecast entries", len(ha_forecast))
        return ha_forecast if ha_forecast else None

    @property
    def forecast(self) -> list | None:
        """Return forecast (deprecated, use async_forecast_hourly)."""
        # For backward compatibility
        forecast_data = self._forecast_coordinator.data if self._forecast_coordinator else []
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
