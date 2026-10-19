"""The meteoswiss integration."""
from __future__ import annotations

import asyncio
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .alerts import MeteoSwissAlertsAPI
from .const import (
    DEFAULT_API_TIMEOUT,
    _create_ssl_connector,
    CONF_DATA_SOURCE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .forecast_coordinator import MeteoSwissForecastCoordinator
from .openmeteo_coordinator import OpenMeteoDataUpdateCoordinator
from .pollen_meteoswiss import MeteoSwissPollenCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.WEATHER,
    Platform.BINARY_SENSOR,
]


def _get_forecast_coordinates(
    hass: HomeAssistant,
    entry: ConfigEntry,
    data_source: str,
) -> tuple[float, float]:
    """Return coordinates used for forecasts and location-based pollen data."""
    if data_source == DATA_SOURCE_METEOSWISS:
        # Observations remain tied to the selected MeteoSwiss station, while
        # forecasts describe the Home Assistant installation location.
        return float(hass.config.latitude), float(hass.config.longitude)

    latitude = entry.data.get(CONF_LATITUDE)
    longitude = entry.data.get(CONF_LONGITUDE)

    # Open-Meteo entries are explicitly location-based. Fall back to the
    # Home Assistant location only for older or incomplete entries.
    if latitude is None:
        latitude = hass.config.latitude
    if longitude is None:
        longitude = hass.config.longitude

    return float(latitude), float(longitude)


async def _async_refresh_optional_coordinators(*coordinators) -> None:
    """Refresh optional coordinators without delaying config entry setup."""
    await asyncio.gather(
        *(coordinator.async_refresh() for coordinator in coordinators),
        return_exceptions=True,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MeteoSwiss integration from a config entry."""
    _LOGGER.info("Setting up MeteoSwiss integration for station %s", entry.data.get(CONF_STATION_NAME))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Create a single shared aiohttp session for all coordinators
    shared_session = aiohttp.ClientSession(
        connector=_create_ssl_connector(),
        timeout=DEFAULT_API_TIMEOUT,
    )

    # Create coordinator based on data source
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, entry.data.get(CONF_UPDATE_INTERVAL, 600))
    data_source = entry.data.get(CONF_DATA_SOURCE, DATA_SOURCE_METEOSWISS)
    station_id = entry.data.get(CONF_STATION_ID)
    post_code = entry.data.get(CONF_POSTAL_CODE)
    lat, lon = _get_forecast_coordinates(hass, entry, data_source)

    if data_source == DATA_SOURCE_OPENMETEO:
        # Use Open-Meteo API for current weather AND forecast
        coordinator = OpenMeteoDataUpdateCoordinator(
            hass,
            latitude=lat,
            longitude=lon,
            update_interval=update_interval,
            session=shared_session,
        )
        _LOGGER.debug("Using Open-Meteo API for lat=%s, lon=%s", lat, lon)

        forecast_coordinator = MeteoSwissForecastCoordinator(
            hass,
            latitude=lat,
            longitude=lon,
            post_code=post_code,
            update_interval=3600,
            session=shared_session,
        )

    else:
        # Use MeteoSwiss API for current weather
        coordinator = MeteoSwissDataUpdateCoordinator(
            hass,
            station_id=station_id,
            update_interval=update_interval,
            session=shared_session,
        )
        _LOGGER.debug("Using MeteoSwiss API for station %s", station_id)

        # Forecasts are location-based and intentionally independent from
        # the selected observation station.
        forecast_coordinator = MeteoSwissForecastCoordinator(
            hass,
            station_id=station_id,
            latitude=lat,
            longitude=lon,
            post_code=post_code,
            update_interval=3600,
            session=shared_session,
        )
        _LOGGER.debug("Forecast coordinator using Home Assistant location: lat=%s, lon=%s", lat, lon)

    # Fetch initial data for current weather
    await coordinator.async_config_entry_first_refresh()

    # Create alerts API and coordinator
    alerts_api = MeteoSwissAlertsAPI(session=shared_session)
    alerts_api.postal_code = post_code

    from .binary_sensor import MeteoSwissAlertsCoordinator
    alerts_coordinator = MeteoSwissAlertsCoordinator(
        hass,
        alerts_api=alerts_api,
        update_interval=600,  # 10 minutes
    )

    # Create pollen API and coordinator (using Open-Meteo Air Quality API)
    from .pollen_coordinator_openmeteo import OpenMeteoPollenCoordinator

    # Location-based pollen forecast follows the same coordinates as weather.
    pollen_coordinator = OpenMeteoPollenCoordinator(
        hass,
        latitude=lat,
        longitude=lon,
        update_interval=1800,  # 30 minutes
        session=shared_session,
    )

    # Create MeteoSwiss measured pollen coordinator
    pollen_station = entry.options.get("pollen_station", "PLZ")
    meteoswiss_pollen_coordinator = MeteoSwissPollenCoordinator(
        hass,
        station_id=pollen_station,
        update_interval=3600,  # 1 hour
        session=shared_session,
    )

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["forecast_coordinator"] = forecast_coordinator
    hass.data[DOMAIN][entry.entry_id]["alerts_coordinator"] = alerts_coordinator
    hass.data[DOMAIN][entry.entry_id]["pollen_coordinator"] = pollen_coordinator
    hass.data[DOMAIN][entry.entry_id]["meteoswiss_pollen_coordinator"] = meteoswiss_pollen_coordinator
    hass.data[DOMAIN][entry.entry_id]["data_source"] = data_source
    hass.data[DOMAIN][entry.entry_id]["session"] = shared_session

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Refresh optional data in parallel after entities are registered
    entry.async_create_background_task(
        hass,
        _async_refresh_optional_coordinators(
            forecast_coordinator,
            alerts_coordinator,
            pollen_coordinator,
            meteoswiss_pollen_coordinator,
        ),
        "MeteoSwiss optional initial refresh",
    )

    # Update listeners for reload
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading MeteoSwiss integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].get(entry.entry_id, {})

        # Close shared session
        session = entry_data.get("session")
        if session and not session.closed:
            await session.close()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
