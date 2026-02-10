"""Weather platform for meteoswiss integration."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.weather import WeatherEntity
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
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
    forecast_coordinator = MeteoSwissForecastCoordinator(
        hass,
        station_id=entry.data.get("station_id"),
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

    @property
    def coordinator_data(self) -> dict:
        """Return coordinator data."""
        return self.coordinator.data if self.coordinator else {}

    @property
    def condition(self) -> str | None:
        """Return current condition."""
        if self.coordinator_data:
            precip = self.coordinator_data.get(SENSOR_PRECIPITATION)
            if precip and precip > 0:
                return "rainy"
            return "sunny"
        return None

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

    @property
    def forecast(self) -> list | None:
        """Return forecast."""
        forecast_data = self._forecast_coordinator.data if self._forecast_coordinator else []

        if not forecast_data:
            return None

        # Convert to HA forecast format (simplified)
        ha_forecast = []
        for entry in forecast_data[:24]:  # Limit to 24 hours
            if entry.get("datetime") and entry.get("temperature") is not None:
                ha_forecast.append({
                    "datetime": entry["datetime"],
                    "temperature": entry["temperature"],
                    "precipitation": entry.get("precipitation"),
                })

        return ha_forecast
