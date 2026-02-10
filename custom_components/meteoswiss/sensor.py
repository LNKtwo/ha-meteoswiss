"""Sensor platform for meteoswiss integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
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


@dataclass
class MeteoSwissSensorEntityDescription(SensorEntityDescription):
    """Describes meteoswiss sensor entity."""

    value_key: str | None = None


SENSOR_DESCRIPTIONS: Final[tuple[MeteoSwissSensorEntityDescription, ...]] = (
    MeteoSwissSensorEntityDescription(
        key=SENSOR_TEMPERATURE,
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_key=SENSOR_TEMPERATURE,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_HUMIDITY,
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_key=SENSOR_HUMIDITY,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_WIND_SPEED,
        translation_key="wind_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_key=SENSOR_WIND_SPEED,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_WIND_DIRECTION,
        translation_key="wind_direction",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        value_key=SENSOR_WIND_DIRECTION,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_PRESSURE,
        translation_key="pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        value_key=SENSOR_PRESSURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    **kwargs,
) -> bool:
    """Set up sensor platform."""
    _LOGGER.info("Setting up MeteoSwiss sensor platform for %s", entry.data.get(CONF_STATION_NAME))

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    hass.data[DOMAIN][entry.entry_id]["sensor_entities"] = [
        MeteoSwissSensor(coordinator, entry, description, station_name)
        for description in SENSOR_DESCRIPTIONS
    ]

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


class MeteoSwissSensor(CoordinatorEntity[MeteoSwissDataUpdateCoordinator], SensorEntity):
    """Representation of a meteoswiss sensor."""

    def __init__(
        self,
        coordinator: MeteoSwissDataUpdateCoordinator,
        entry: ConfigEntry,
        description: MeteoSwissSensorEntityDescription,
        station_name: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="SwissMetNet",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        if self.coordinator.data:
            value = self.coordinator.data.get(self.entity_description.value_key)
            self._attr_native_value = value
        super()._handle_coordinator_update()
