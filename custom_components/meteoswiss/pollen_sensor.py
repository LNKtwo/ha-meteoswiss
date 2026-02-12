"""Pollen sensor platform for MeteoSwiss integration."""
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
    EntityCategory,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTRIBUTION,
    CONF_POSTAL_CODE,
    CONF_STATION_NAME,
    DOMAIN,
)
from .pollen import (
    MeteoSwissPollenAPI,
    PollenMeasurement,
    POLLEN_AMBROSIA,
    POLLEN_ALDER,
    POLLEN_BIRCH,
    POLLEN_GRASS,
    POLLEN_HAZEL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MeteoSwissPollenSensorEntityDescription(SensorEntityDescription):
    """Describes MeteoSwiss pollen sensor."""

    pollen_type: str
    pollen_type_name: str


POLLEN_SENSOR_DESCRIPTIONS: Final[tuple[MeteoSwissPollenSensorEntityDescription, ...]] = (
    MeteoSwissPollenSensorEntityDescription(
        key=POLLEN_BIRCH,
        translation_key="pollen_birch",
        name="Birch Pollen",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUND,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="",
        icon="mdi:tree",
        pollen_type=POLLEN_BIRCH,
        pollen_type_name="Birch",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key=POLLEN_HAZEL,
        translation_key="pollen_hazel",
        name="Hazel Pollen",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUND,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="",
        icon="mdi:tree-outline",
        pollen_type=POLLEN_HAZEL,
        pollen_type_name="Hazel",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key=POLLEN_ALDER,
        translation_key="pollen_alder",
        name="Alder Pollen",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUND,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="",
        icon="mdi:pine-tree",
        pollen_type=POLLEN_ALDER,
        pollen_type_name="Alder",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key=POLLEN_GRASS,
        translation_key="pollen_grass",
        name="Grass Pollen",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUND,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="",
        icon="mdi:grass",
        pollen_type=POLLEN_GRASS,
        pollen_type_name="Grass",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key=POLLEN_AMBROSIA,
        translation_key="pollen_ambrosia",
        name="Ambrosia Pollen",
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUND,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="",
        icon="mdi:flower",
        pollen_type=POLLEN_AMBROSIA,
        pollen_type_name="Ambrosia",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up pollen sensor platform."""
    _LOGGER.info("Setting up MeteoSwiss pollen sensor platform for %s", entry.data.get(CONF_STATION_NAME))

    coordinator = hass.data[DOMAIN][entry.entry_id].get("pollen_coordinator")

    if coordinator is None:
        _LOGGER.warning("Pollen coordinator not found - pollen sensors not available")
        return

    postal_code = entry.data.get(CONF_POSTAL_CODE)
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    entities = [
        MeteoSwissPollenSensor(coordinator, entry, description, station_name)
        for description in POLLEN_SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class MeteoSwissPollenSensor(SensorEntity):
    """Representation of a MeteoSwiss pollen sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, PollenMeasurement]],
        entry: ConfigEntry,
        description: MeteoSwissPollenSensorEntityDescription,
        station_name: str,
    ) -> None:
        """Initialize pollen sensor."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_pollen_{description.pollen_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"pollen_{entry.entry_id}")},
            name=f"MeteoSwiss Pollen - {station_name}",
            manufacturer="MeteoSwiss",
            model="Pollen Forecast",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._attr_entity_category = EntityCategory.HEALTH
        self._pollen_type = description.pollen_type
        self._pollen_type_name = description.pollen_type_name

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        pollen_data = self.coordinator.data
        measurement = pollen_data.get(self._pollen_type)

        if measurement is None:
            return "No data"

        if measurement.value is None:
            return "Not active"

        return measurement.level_name or f"Level {measurement.level}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self.async_write_ha_state()
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {}

        pollen_data = self.coordinator.data
        measurement = pollen_data.get(self._pollen_type)

        if measurement is None:
            return {
                "pollen_type": self._pollen_type,
                "pollen_type_name": self._pollen_type_name,
                "active": False,
            }

        return {
            "pollen_type": self._pollen_type,
            "pollen_type_name": self._pollen_type_name,
            "level": measurement.level,
            "level_name": measurement.level_name,
            "value": measurement.value,
            "is_high_risk": measurement.is_high_risk() if hasattr(measurement, 'is_high_risk') else False,
            "active": measurement.is_active() if hasattr(measurement, 'is_active') else False,
        }
