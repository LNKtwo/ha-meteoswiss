"""Sensor platform for meteoswiss integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
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
    from homeassistant.components.sensor import SensorDeviceClass as _SDC
    _CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = getattr(
        _SDC, "CONCENTRATION_MICROGRAMS_PER_CUBIC_METER", "µg/m³"
    )
except ImportError:
    _CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = "µg/m³"

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
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .cache import get_all_cache_stats
from .const import (
    ATTRIBUTION,
    CONF_DATA_SOURCE,
    CONF_STATION_NAME,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
    SENSOR_DEW_POINT,
    SENSOR_FOEHN_INDEX,
    SENSOR_GLOBAL_RADIATION,
    SENSOR_HUMIDITY,
    SENSOR_NITROGEN_DIOXIDE,
    SENSOR_OZONE,
    SENSOR_PM10,
    SENSOR_PM25,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_SNOW_DEPTH,
    SENSOR_SUNSHINE,
    SENSOR_TEMPERATURE,
    SENSOR_UV_INDEX,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_GUST,
    SENSOR_WIND_SPEED,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .stations_map import MeteoSwissStationsMap
from .calc import (
    calculate_heating_degree_days,
    get_heating_season_start_date,
    is_in_heating_season,
)

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
        key=SENSOR_SNOW_DEPTH,
        translation_key="snow_depth",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        value_key=SENSOR_SNOW_DEPTH,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_FOEHN_INDEX,
        translation_key="foehn_index",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="Code",
        value_key=SENSOR_FOEHN_INDEX,
    ),
    # Soil temperature sensors removed — most SwissMetNet stations
    # (including LUZ) don't measure soil temperatures. Only a few stations
    # have probes at 5/10/20 cm depth. If needed, add back manually.
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

    # Add air quality sensors (from pollen/AQ coordinator)
    if pollen_coordinator:
        entities.extend(
            MeteoSwissAirQualitySensor(pollen_coordinator, entry, description, station_name)
            for description in AIR_QUALITY_SENSOR_DESCRIPTIONS
        )
        _LOGGER.debug("Added %d air quality sensors", len(AIR_QUALITY_SENSOR_DESCRIPTIONS))

    # Add heating degree days sensors
    forecast_coordinator = hass.data[DOMAIN][entry.entry_id].get("forecast_coordinator")
    if forecast_coordinator:
        entities.append(
            MeteoSwissHeatingDegreeDaysSensor(forecast_coordinator, entry, station_name)
        )
        entities.append(
            MeteoSwissSeasonHgtSensor(forecast_coordinator, entry, station_name)
        )
        _LOGGER.debug("Added heating degree days sensors")

    # Add MeteoSwiss measured pollen sensors
    ms_pollen_coordinator = hass.data[DOMAIN][entry.entry_id].get("meteoswiss_pollen_coordinator")
    if ms_pollen_coordinator:
        for description in MS_POLLEN_SENSOR_DESCRIPTIONS:
            entities.append(
                MeteoSwissMeasuredPollenSensor(ms_pollen_coordinator, entry, description, station_name)
            )
        _LOGGER.debug("Added %d MeteoSwiss measured pollen sensors", len(MS_POLLEN_SENSOR_DESCRIPTIONS))

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


# --------------------------------------------------------------------------- #
# Air Quality Sensors (from Open-Meteo Air Quality API)                       #
# --------------------------------------------------------------------------- #

AIR_QUALITY_SENSOR_DESCRIPTIONS: Final[tuple[MeteoSwissSensorEntityDescription, ...]] = (
    MeteoSwissSensorEntityDescription(
        key=SENSOR_PM25,
        translation_key="pm25",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        value_key=SENSOR_PM25,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_PM10,
        translation_key="pm10",
        device_class=SensorDeviceClass.PM10,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        value_key=SENSOR_PM10,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_NITROGEN_DIOXIDE,
        translation_key="nitrogen_dioxide",
        device_class=SensorDeviceClass.NITROGEN_DIOXIDE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        value_key=SENSOR_NITROGEN_DIOXIDE,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_OZONE,
        translation_key="ozone",
        device_class=SensorDeviceClass.OZONE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=_CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        value_key=SENSOR_OZONE,
    ),
    MeteoSwissSensorEntityDescription(
        key=SENSOR_UV_INDEX,
        translation_key="uv_index",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="UV Index",
        value_key="uv_index",
    ),
)


class MeteoSwissAirQualitySensor(CoordinatorEntity, SensorEntity):
    """Representation of a MeteoSwiss air quality sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: MeteoSwissSensorEntityDescription,
        station_name: str,
    ) -> None:
        """Initialize air quality sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"pollen_{entry.entry_id}")},
            name=f"MeteoSwiss Air Quality - {station_name}",
            manufacturer="MeteoSwiss",
            model="Open-Meteo Air Quality",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = "Source: Open-Meteo Air Quality API"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        if self.coordinator.data:
            value_key = self.entity_description.value_key
            value = self.coordinator.data.get(value_key)
            self._attr_native_value = value
        else:
            self._attr_native_value = None
        super()._handle_coordinator_update()


# --------------------------------------------------------------------------- #
# Heating Degree Days (Heizgradtage) Sensors                                   #
# --------------------------------------------------------------------------- #

class MeteoSwissHeatingDegreeDaysSensor(CoordinatorEntity, SensorEntity):
    """Sensor for daily heating degree days (SIA 381/3)."""

    def __init__(
        self,
        forecast_coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        station_name: str,
    ) -> None:
        super().__init__(forecast_coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_heating_degree_days"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="Heizgradtage",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self.entity_description = SensorEntityDescription(
            key="heating_degree_days",
            translation_key="heating_degree_days",
            device_class=None,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="°C·d",
            icon="mdi:thermostat",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Calculate HGt from forecast daily mean temperature."""
        if not self.coordinator.data:
            self._attr_native_value = None
            self._attr_extra_state_attributes = None
            super()._handle_coordinator_update()
            return

        # Use today's forecast entries to compute daily mean
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_temps = [
            e.get("temperature")
            for e in self.coordinator.data
            if e.get("datetime", "").startswith(today_str) and e.get("temperature") is not None
        ]

        if today_temps:
            daily_mean = sum(today_temps) / len(today_temps)
            hgt = calculate_heating_degree_days(daily_mean)
            self._attr_native_value = round(hgt, 1) if hgt is not None else None
            self._attr_extra_state_attributes = {
                "daily_mean_temp": round(daily_mean, 1),
                "heating_threshold": 12.0,
                "in_heating_season": is_in_heating_season(),
            }
        else:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "in_heating_season": is_in_heating_season(),
            }

        super()._handle_coordinator_update()


class MeteoSwissSeasonHgtSensor(CoordinatorEntity, SensorEntity):
    """Sensor for accumulated heating degree days since heating season start."""

    def __init__(
        self,
        forecast_coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        station_name: str,
    ) -> None:
        super().__init__(forecast_coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_season_hgt"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="Heizgradtage Saison",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self.entity_description = SensorEntityDescription(
            key="season_hgt",
            translation_key="season_heating_degree_days",
            device_class=None,
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement="°C·d",
            icon="mdi:calendar-sync",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Calculate season accumulated HGt."""
        if not self.coordinator.data:
            self._attr_native_value = None
            self._attr_extra_state_attributes = None
            super()._handle_coordinator_update()
            return

        # Compute season start
        season_start = get_heating_season_start_date()

        # We only have forecast data (5 days), so we can only estimate
        # For a proper season total, we'd need historical daily data.
        # For now, compute HGt for available forecast days that fall in heating season.
        season_hgt = 0.0
        days_counted = 0

        # Group forecast entries by day
        daily_means: dict[str, list[float]] = {}
        for entry_data in self.coordinator.data:
            dt_str = entry_data.get("datetime", "")
            temp = entry_data.get("temperature")
            if not dt_str or temp is None:
                continue
            day_str = dt_str[:10]
            daily_means.setdefault(day_str, []).append(temp)

        today_str = datetime.now().strftime("%Y-%m-%d")
        today_hgt = 0.0

        for day_str, temps in sorted(daily_means.items()):
            try:
                day_date = date.fromisoformat(day_str)
            except ValueError:
                continue

            if day_date < season_start:
                continue
            if day_date > date.today():
                # Include future forecast days as estimates
                pass

            daily_mean = sum(temps) / len(temps)
            hgt = calculate_heating_degree_days(daily_mean)
            if hgt is not None:
                season_hgt += hgt
                days_counted += 1
                if day_str == today_str:
                    today_hgt = hgt

        self._attr_native_value = round(season_hgt, 1)
        self._attr_extra_state_attributes = {
            "season_start": season_start.isoformat(),
            "days_counted": days_counted,
            "today_hgt": round(today_hgt, 1),
            "note": "Based on available forecast data only. For full season total, historical daily data is needed.",
        }

        super()._handle_coordinator_update()


# --------------------------------------------------------------------------- #
# MeteoSwiss Measured Pollen Sensors                                          #
# --------------------------------------------------------------------------- #


@dataclass
class MS_PollenSensorDescription(SensorEntityDescription):
    """Describes a MeteoSwiss measured pollen sensor."""

    pollen_type: str = ""
    pollen_type_name: str = ""


MS_POLLEN_SENSOR_DESCRIPTIONS: Final[tuple[MS_PollenSensorDescription, ...]] = (
    MS_PollenSensorDescription(
        key="ms_pollen_birch",
        translation_key="ms_pollen_birch",
        name="Birch Pollen (Measured)",
        icon="mdi:tree",
        pollen_type="birch",
        pollen_type_name="Birch",
    ),
    MS_PollenSensorDescription(
        key="ms_pollen_alder",
        translation_key="ms_pollen_alder",
        name="Alder Pollen (Measured)",
        icon="mdi:pine-tree",
        pollen_type="alder",
        pollen_type_name="Alder",
    ),
    MS_PollenSensorDescription(
        key="ms_pollen_hazel",
        translation_key="ms_pollen_hazel",
        name="Hazel Pollen (Measured)",
        icon="mdi:branch",
        pollen_type="hazel",
        pollen_type_name="Hazel",
    ),
    MS_PollenSensorDescription(
        key="ms_pollen_grass",
        translation_key="ms_pollen_grass",
        name="Grass Pollen (Measured)",
        icon="mdi:grass",
        pollen_type="grass",
        pollen_type_name="Grass",
    ),
    MS_PollenSensorDescription(
        key="ms_pollen_beech",
        translation_key="ms_pollen_beech",
        name="Beech Pollen (Measured)",
        icon="mdi:tree-outline",
        pollen_type="beech",
        pollen_type_name="Beech",
    ),
    MS_PollenSensorDescription(
        key="ms_pollen_ash",
        translation_key="ms_pollen_ash",
        name="Ash Pollen (Measured)",
        icon="mdi:leaf",
        pollen_type="ash",
        pollen_type_name="Ash",
    ),
)


class MeteoSwissMeasuredPollenSensor(CoordinatorEntity, SensorEntity):
    """Representation of a MeteoSwiss measured pollen sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        description: MS_PollenSensorDescription,
        station_name: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_ms_pollen_{description.pollen_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"ms_pollen_{entry.entry_id}")},
            name=f"MeteoSwiss Pollen (Measured) - {station_name}",
            manufacturer="MeteoSwiss",
            model="Pollen Station",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = "Source: MeteoSwiss ogd-pollen"
        try:
            self._attr_entity_category = EntityCategory.HEALTH
        except AttributeError:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._pollen_type = description.pollen_type
        self._pollen_type_name = description.pollen_type_name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        if self.coordinator.data:
            pollen_data = self.coordinator.data.get(self._pollen_type)
            if pollen_data and isinstance(pollen_data, dict):
                self._attr_native_value = pollen_data.get("current")
                self._attr_extra_state_attributes = {
                    "pollen_type": self._pollen_type,
                    "pollen_type_name": self._pollen_type_name,
                    "unit": pollen_data.get("unit", "No/m³"),
                    "source": pollen_data.get("source", "MeteoSwiss measured"),
                    "history_24h": pollen_data.get("history_24h", []),
                    "station": self.coordinator.data.get("station_id", ""),
                    "last_update": self.coordinator.data.get("last_update", ""),
                }
            else:
                self._attr_native_value = None
                self._attr_extra_state_attributes = {
                    "pollen_type": self._pollen_type,
                    "pollen_type_name": self._pollen_type_name,
                    "station": self.coordinator.data.get("station_id", "") if self.coordinator.data else "",
                }
        else:
            self._attr_native_value = None

        super()._handle_coordinator_update()
