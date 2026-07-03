"""Sensor platform for meteoswiss integration."""
from __future__ import annotations

import json
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

try:
    from homeassistant.const import UnitOfIrradiance
except ImportError:
    UnitOfIrradiance = type("UnitOfIrradiance", (), {"WATTS_PER_SQUARE_METER": "W/m²"})

try:
    from homeassistant.const import UnitOfTime
except ImportError:
    UnitOfTime = type("UnitOfTime", (), {"MINUTES": "min", "HOURS": "h", "DAYS": "d"})

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .cache import get_all_cache_stats
from .const import (
    ATTRIBUTION,
    CONF_DATA_SOURCE,
    CONF_STATION_NAME,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
    SENSOR_DEW_POINT,
    SENSOR_GLOBAL_RADIATION,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_SUNSHINE,
    SENSOR_TEMPERATURE,
    SENSOR_UV_INDEX,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_GUST,
    SENSOR_WIND_SPEED,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .stations_map import MeteoSwissStationsMap

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
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="°",
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
    MeteoSwissSensorEntityDescription(
        key=SENSOR_WIND_GUST,
        translation_key="wind_gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_key=SENSOR_WIND_GUST,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_DEW_POINT,
        translation_key="dew_point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_key=SENSOR_DEW_POINT,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_SUNSHINE,
        translation_key="sunshine_duration",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_key=SENSOR_SUNSHINE,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_GLOBAL_RADIATION,
        translation_key="global_radiation",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        value_key=SENSOR_GLOBAL_RADIATION,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_UV_INDEX,
        translation_key="uv_index",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="UV Index",
        value_key=SENSOR_UV_INDEX,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up sensor platform."""
    _LOGGER.debug("Setting up MeteoSwiss sensor platform for %s", entry.data.get(CONF_STATION_NAME))

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    entities = [
        MeteoSwissSensor(coordinator, entry, description, station_name)
        for description in SENSOR_DESCRIPTIONS
    ]

    # Add stations map sensor (only once)
    if not hass.data[DOMAIN].get("stations_map_sensor_added", False):
        from .stations_map import get_stations_map
        stations_map = await get_stations_map()
        stations_map_sensor = MeteoSwissStationsMapSensor(stations_map)
        entities.append(stations_map_sensor)
        hass.data[DOMAIN]["stations_map_sensor_added"] = True
        _LOGGER.debug("Added stations map sensor")

    # Add cache stats sensor (only once)
    if not hass.data[DOMAIN].get("cache_stats_sensor_added", False):
        cache_stats_sensor = MeteoSwissCacheStatsSensor()
        entities.append(cache_stats_sensor)
        hass.data[DOMAIN]["cache_stats_sensor_added"] = True
        _LOGGER.debug("Added cache stats sensor")

    # Add pollen sensors
    pollen_coordinator = hass.data[DOMAIN][entry.entry_id].get("pollen_coordinator")
    if pollen_coordinator:
        from .pollen_sensor import POLLEN_SENSOR_DESCRIPTIONS, MeteoSwissPollenSensor
        for description in POLLEN_SENSOR_DESCRIPTIONS:
            entities.append(
                MeteoSwissPollenSensor(pollen_coordinator, entry, description, station_name)
            )
        _LOGGER.debug("Added %d pollen sensors", len(POLLEN_SENSOR_DESCRIPTIONS))

    async_add_entities(entities)


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
            value_key = self.entity_description.value_key
            value = self.coordinator.data.get(value_key)
            self._attr_native_value = value
        else:
            _LOGGER.debug("Coordinator data is None or empty for %s", self.entity_description.key)
            self._attr_native_value = None

        super()._handle_coordinator_update()


class MeteoSwissStationsMapSensor(SensorEntity):
    """Representation of a meteoswiss stations map sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, stations_map: MeteoSwissStationsMap) -> None:
        """Initialize stations map sensor."""
        self._stations_map = stations_map
        self._attr_unique_id = f"{DOMAIN}_stations_map"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "stations_map")},
            name="MeteoSwiss Weather Stations",
            manufacturer="MeteoSwiss",
            model="SwissMetNet",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._attr_name = "Weather Stations"
        self._attr_native_value = "Loading..."

    async def async_update(self) -> None:
        """Update stations map."""
        _LOGGER.debug("Updating stations map")

        await self._stations_map.load_stations()
        stations = self._stations_map.get_all_stations()

        # Update native value with station count
        self._attr_native_value = f"{len(stations)} stations"
        self._attr_extra_state_attributes = {
            "station_count": len(stations),
            "stations": [s.to_dict() for s in stations[:20]],  # Limit to first 20
            "geojson": self._stations_map.to_geojson(),
            "picture_elements_config": self._stations_map.to_picture_elements_config(),
        }

        _LOGGER.debug("Stations map updated: %d stations", len(stations))


class MeteoSwissCacheStatsSensor(SensorEntity):
    """Representation of cache statistics sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self) -> None:
        """Initialize cache stats sensor."""
        self._attr_unique_id = f"{DOMAIN}_cache_stats"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "cache_stats")},
            name="MeteoSwiss Cache Statistics",
            manufacturer="MeteoSwiss",
            model="Intelligent Caching",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._attr_name = "Cache Statistics"
        self._attr_native_value = "Running"

    async def async_update(self) -> None:
        """Update cache statistics."""
        _LOGGER.debug("Updating cache statistics")

        stats = get_all_cache_stats()

        # Calculate overall hit rate
        total_hits = stats["current_weather"]["hits"] + stats["forecast"]["hits"]
        total_misses = stats["current_weather"]["misses"] + stats["forecast"]["misses"]
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

        self._attr_native_value = f"{overall_hit_rate:.1f}% hit rate"
        self._attr_extra_state_attributes = {
            "overall_hit_rate": round(overall_hit_rate, 2),
            "current_weather": stats["current_weather"],
            "forecast": stats["forecast"],
            "stations": stats["stations"],
        }
