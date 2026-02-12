"""Binary sensor platform for MeteoSwiss weather alerts."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .alerts import MeteoSwissAlertsAPI, WeatherAlert
from .const import (
    ATTRIBUTION,
    CONF_POSTAL_CODE,
    CONF_STATION_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MeteoSwissAlertsBinarySensorDescription(BinarySensorEntityDescription):
    """Describes MeteoSwiss alerts binary sensor."""

    warn_level: int | None = None
    warn_type: int | None = None


ALERT_SENSOR_DESCRIPTIONS: Final[tuple[MeteoSwissAlertsBinarySensorDescription, ...]] = (
    MeteoSwissAlertsBinarySensorDescription(
        key="any_alert",
        translation_key="any_alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        name="Weather Alert",
        icon="mdi:alert",
    ),
    MeteoSwissAlertsBinarySensorDescription(
        key="critical_alert",
        translation_key="critical_alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        name="Critical Weather Alert",
        icon="mdi:alert-octagram",
        warn_level=3,  # Level 3 or above
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up binary sensor platform."""
    _LOGGER.info("Setting up MeteoSwiss alerts binary sensor platform for %s", entry.data.get(CONF_STATION_NAME))

    coordinator = hass.data[DOMAIN][entry.entry_id]["alerts_coordinator"]
    postal_code = entry.data.get(CONF_POSTAL_CODE)

    entities = [
        MeteoSwissAlertsBinarySensor(coordinator, entry, description, postal_code)
        for description in ALERT_SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class MeteoSwissAlertsBinarySensor(BinarySensorEntity):
    """Representation of a MeteoSwiss weather alert binary sensor."""

    def __init__(
        self,
        coordinator: MeteoSwissAlertsCoordinator,
        entry: ConfigEntry,
        description: MeteoSwissAlertsBinarySensorDescription,
        postal_code: str,
    ) -> None:
        """Initialize binary sensor."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"alerts_{entry.entry_id}")},
            name=f"MeteoSwiss Alerts - {postal_code}",
            manufacturer="MeteoSwiss",
            model="Alerts",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._postal_code = postal_code

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return False

        alerts = self.coordinator.data

        if not alerts:
            return False

        # Check if any alert matches the criteria
        warn_level = self.entity_description.warn_level
        warn_type = self.entity_description.warn_type

        for alert in alerts:
            if alert.outlook:
                continue  # Ignore outlooks

            if warn_level is not None and alert.warn_level < warn_level:
                continue

            if warn_type is not None and alert.warn_type != warn_type:
                continue

            return True  # Alert matches criteria

        return False

    @property
    def extra_state_attributes(self) -> dict[str, str | int] | None:
        """Return the state attributes."""
        alerts = self.coordinator.data

        if not alerts:
            return {
                "active_alerts_count": 0,
                "alerts": [],
            }

        active_alerts = [a.to_dict() for a in alerts if not a.outlook and a.is_active()]

        return {
            "active_alerts_count": len(active_alerts),
            "alerts": active_alerts,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self.async_write_ha_state()
        super()._handle_coordinator_update()


class MeteoSwissAlertsCoordinator(DataUpdateCoordinator[list[WeatherAlert]]):
    """Class to manage fetching MeteoSwiss alerts."""

    def __init__(
        self,
        hass: HomeAssistant,
        alerts_api: MeteoSwissAlertsAPI,
        update_interval: int = 600,
    ) -> None:
        """Initialize."""
        self._alerts_api = alerts_api

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_alerts",
            update_interval=update_interval,  # 10 minutes
        )

    async def _async_update_data(self) -> list[WeatherAlert]:
        """Fetch alerts from MeteoSwiss App API."""
        _LOGGER.info("Fetching MeteoSwiss alerts")

        alerts = await self._alerts_api.get_alerts(self._alerts_api.postal_code)

        _LOGGER.info("Successfully fetched %d MeteoSwiss alerts", len(alerts))

        return alerts

    async def async_close(self) -> None:
        """Close alerts API session."""
        await self._alerts_api.close()
