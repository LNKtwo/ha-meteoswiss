"""Weather platform for MeteoSwiss integration."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
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

# Condition mapping based on MeteoSwiss data
CONDITION_MAP: Final = {
    "clear": "sunny",
    "cloudy": "cloudy",
    "rain": "rainy",
    "snow": "snowy",
    "fog": "foggy",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up weather platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    station_name = entry.data[CONF_STATION_NAME]

    hass.data[DOMAIN][entry.entry_id]["weather_entity"] = MeteoSwissWeather(
        coordinator, entry, station_name
    )

    await hass.config_entries.async_forward_entry_setups(entry, ["weather"])
    return True


class MeteoSwissWeather(CoordinatorEntity[MeteoSwissDataUpdateCoordinator], WeatherEntity):
    """Representation of MeteoSwiss weather data."""

    def __init__(
        self,
        coordinator: MeteoSwissDataUpdateCoordinator,
        entry: ConfigEntry,
        station_name: str,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="SwissMetNet",
        )
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_weather"
        self._attr_has_entity_name = True
        self._attr_name = None
        self._attr_attribution = ATTRIBUTION

        # Set units
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            data = self.coordinator.data

            self._attr_native_temperature = data.get(SENSOR_TEMPERATURE)
            self._attr_native_pressure = data.get(SENSOR_PRESSURE)
            self._attr_native_wind_speed = data.get(SENSOR_WIND_SPEED)
            self._attr_native_wind_bearing = data.get(SENSOR_WIND_DIRECTION)
            self._attr_native_humidity = data.get(SENSOR_HUMIDITY)
            self._attr_native_precipitation_unit = "mm"
            self._attr_native_precipitation = data.get(SENSOR_PRECIPITATION)

            # Determine condition based on data
            # This is a simplified logic - will need to be enhanced
            self._attr_condition = self._determine_condition(data)

        super()._handle_coordinator_update()

    def _determine_condition(self, data: dict) -> str:
        """Determine weather condition from data."""
        # This is a simplified implementation
        # Real implementation should use MeteoSwiss weather codes
        temp = data.get(SENSOR_TEMPERATURE)
        humidity = data.get(SENSOR_HUMIDITY)
        precipitation = data.get(SENSOR_PRECIPITATION)

        if precipitation and precipitation > 0:
            if temp and temp < 0:
                return "snowy"
            return "rainy"

        if humidity and humidity > 90:
            return "foggy"

        # Default to partly cloudy for now
        return "partlycloudy"
