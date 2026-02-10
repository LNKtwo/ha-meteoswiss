"""The meteoswiss integration."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from .pollen import MeteoSwissClient
from .coordinator import MeteoSwissDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.WEATHER,
]

# Load forecast_coordinator
from .forecast_coordinator import MeteoSwissForecastCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MeteoSwiss integration from a config entry."""
    _LOGGER.info("Setting up MeteoSwiss integration for station %s", entry.data.get(CONF_STATION_NAME))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Create coordinator
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, 600)
    station_id = entry.data[CONF_STATION_ID]

    coordinator = MeteoSwissDataUpdateCoordinator(
        hass,
        station_id=station_id,
        update_interval=update_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["session"] = None

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Update listeners for reload
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading MeteoSwiss integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
