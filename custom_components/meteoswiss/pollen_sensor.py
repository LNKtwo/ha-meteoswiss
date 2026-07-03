"""Pollen sensor platform for MeteoSwiss integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTRIBUTION,
    CONF_POSTAL_CODE,
    CONF_STATION_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Pollen types matching Open-Meteo Air Quality API parameter names
POLLEN_BIRCH = "birch_pollen"
POLLEN_ALDER = "alder_pollen"
POLLEN_GRASS = "grass_pollen"
POLLEN_MUGWORT = "mugwort_pollen"
POLLEN_RAGWEED = "ragweed_pollen"


# Pollen level thresholds (grains/m³)
def _pollen_level(value: float | None, low: float, mod: float, high: float) -> str:
    """Convert pollen concentration to level name."""
    if value is None or value == 0:
        return "None"
    elif value < low:
        return "Low"
    elif value < mod:
        return "Moderate"
    elif value < high:
        return "High"
    else:
        return "Very High"


# Thresholds per pollen type (grains/m³)
# Based on standard allergological thresholds
POLLEN_THRESHOLDS = {
    POLLEN_BIRCH: (10, 50, 200),
    POLLEN_ALDER: (10, 50, 200),
    POLLEN_GRASS: (5, 20, 50),
    POLLEN_MUGWORT: (10, 50, 200),
    POLLEN_RAGWEED: (5, 20, 50),
}


@dataclass
class MeteoSwissPollenSensorEntityDescription(SensorEntityDescription):
    """Describes MeteoSwiss pollen sensor."""

    pollen_type: str = ""
    pollen_type_name: str = ""


POLLEN_SENSOR_DESCRIPTIONS: Final[tuple[MeteoSwissPollenSensorEntityDescription, ...]] = (
    MeteoSwissPollenSensorEntityDescription(
        key="birch_pollen",
        translation_key="pollen_birch",
        name="Birch Pollen",
        icon="mdi:tree",
        pollen_type=POLLEN_BIRCH,
        pollen_type_name="Birch",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key="alder_pollen",
        translation_key="pollen_alder",
        name="Alder Pollen",
        icon="mdi:pine-tree",
        pollen_type=POLLEN_ALDER,
        pollen_type_name="Alder",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key="grass_pollen",
        translation_key="pollen_grass",
        name="Grass Pollen",
        icon="mdi:grass",
        pollen_type=POLLEN_GRASS,
        pollen_type_name="Grass",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key="mugwort_pollen",
        translation_key="pollen_mugwort",
        name="Mugwort Pollen",
        icon="mdi:flower",
        pollen_type=POLLEN_MUGWORT,
        pollen_type_name="Mugwort",
    ),
    MeteoSwissPollenSensorEntityDescription(
        key="ragweed_pollen",
        translation_key="pollen_ambrosia",
        name="Ragweed Pollen",
        icon="mdi:sprout",
        pollen_type=POLLEN_RAGWEED,
        pollen_type_name="Ragweed",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up pollen sensor platform."""
    _LOGGER.debug("Setting up MeteoSwiss pollen sensor platform for %s", entry.data.get(CONF_STATION_NAME))

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
        try:
            self._attr_entity_category = EntityCategory.HEALTH
        except AttributeError:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._pollen_type = description.pollen_type
        self._pollen_type_name = description.pollen_type_name

    @property
    def native_value(self) -> float | None:
        """Return the current pollen concentration (grains/m³)."""
        if self.coordinator.data is None:
            return None

        pollen_data = self.coordinator.data.get(self._pollen_type)

        if pollen_data is None:
            return None

        current = pollen_data.get("current")
        return current if current is not None else None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self.async_write_ha_state()
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return None

        pollen_data = self.coordinator.data.get(self._pollen_type)

        if pollen_data is None:
            return {
                "pollen_type": self._pollen_type,
                "pollen_type_name": self._pollen_type_name,
                "level": None,
                "level_name": "No data",
                "unit": "grains/m³",
            }

        current = pollen_data.get("current", 0)
        thresholds = POLLEN_THRESHOLDS.get(self._pollen_type, (5, 20, 50))
        level_name = _pollen_level(current, *thresholds)

        return {
            "pollen_type": self._pollen_type,
            "pollen_type_name": self._pollen_type_name,
            "level_name": level_name,
            "unit": pollen_data.get("unit", "grains/m³"),
            "forecast_24h": pollen_data.get("forecast", [])[:24],
        }
