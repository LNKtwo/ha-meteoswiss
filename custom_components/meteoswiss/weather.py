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

_LOGGER = logging.getLogger(__name__)

# Condition mapping
CONDITION_MAP: Final = {
    "clear": "sunny",
    "cloudy": "cloudy",
    "rain": "rainy",
    "snow": "snowy",
    "fog": "foggy",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *args,
) -> bool:
    """Set up weather platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    hass.data[DOMAIN][entry.entry_id]["weather_entity"] = MeteoSwissWeather(
        coordinator, entry, station_name
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["weather"])
    return True


class MeteoSwissWeather(CoordinatorEntity[MeteoSwissDataUpdateCoordinator], WeatherEntity):
    """Representation of meteoswiss weather data."""

    def __init__(
        self,
        coordinator: MeteoSwissDataUpdateCoordinator,
        entry: ConfigEntry,
        station_name: str,
    ) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
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
    def condition(self) -> str | None:
        """Return the current condition."""
        if self.coordinator_data:
            # Simple condition mapping based on precipitation
            precip = self.coordinator_data.get(SENSOR_PRECIPITATION)
            if precip and precip > 0:
                return "rainy"
            return "sunny"
        return None

    @property
    def temperature(self) -> float | None:
        """Return the temperature."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_TEMPERATURE)
        return None

    @property
    def pressure(self) -> float | None:
        """Return the pressure."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_PRESSURE)
        return None

    @property
    def humidity(self) -> int | None:
        """Return the humidity."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_HUMIDITY)
        return None

    @property
    def wind_speed(self) -> float | None:
        """Return the wind speed."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_WIND_SPEED)
        return None

    @property
    def wind_bearing(self) -> float | None:
        """Return the wind bearing."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_WIND_DIRECTION)
        return None

    @property
    def forecast(self) -> list | None:
        """Return the forecast."""
        return None
