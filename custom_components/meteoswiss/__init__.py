"""The meteoswiss integration."""
from __future__ import annotations

import logging

import aiohttp
from aiohttp import TCPConnector
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .alerts import MeteoSwissAlertsAPI
from .const import (
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
    STATIONS_METADATA_URL,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .forecast_coordinator import MeteoSwissForecastCoordinator
from .openmeteo_coordinator import OpenMeteoDataUpdateCoordinator
from .pollen import MeteoSwissClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.WEATHER,
    Platform.BINARY_SENSOR,
]


def _create_ssl_connector() -> TCPConnector:
    """Create a new SSL connector for each session to avoid reuse issues."""
    return TCPConnector(ssl=False)


async def _load_station_coordinates(station_id: str) -> tuple[float | None, float | None]:
    """Load station coordinates from MeteoSwiss metadata CSV."""
    try:
        async with aiohttp.ClientSession(connector=_create_ssl_connector()) as session:
            async with session.get(STATIONS_METADATA_URL) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to load stations: %s", response.status)
                    return None, None

                content_bytes = await response.read()

        # Try different encodings for CSV
        lines = None
        for encoding in ['iso-8859-1', 'latin-1', 'cp1252', 'utf-8-sig', 'utf-8']:
            try:
                decoded = content_bytes.decode(encoding)
                lines = decoded.strip().split("\n")
                if len(lines) > 10:
                    break
            except UnicodeDecodeError:
                continue

        if not lines or len(lines) < 2:
            _LOGGER.error("Failed to decode stations CSV")
            return None, None

        # Parse CSV to find station coordinates
        station_id_lower = station_id.lower()
        for line in lines[1:]:
            parts = line.split(";")
            if len(parts) > 15:
                csv_station_id = parts[0].strip().lower()
                if csv_station_id == station_id_lower:
                    # Coordinates at indices 14 (lat) and 15 (lon)
                    try:
                        lat = float(parts[14]) if parts[14] else None
                        lon = float(parts[15]) if parts[15] else None
                        _LOGGER.info("Found coordinates for station %s: lat=%s, lon=%s", station_id, lat, lon)
                        return lat, lon
                    except (ValueError, TypeError) as e:
                        _LOGGER.error("Could not parse coordinates: %s", e)
                        return None, None

        _LOGGER.warning("Station %s not found in metadata", station_id)
        return None, None

    except Exception as err:
        _LOGGER.error("Error loading station coordinates: %s", err)
        return None, None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MeteoSwiss integration from a config entry."""
    _LOGGER.info("Setting up MeteoSwiss integration for station %s", entry.data.get(CONF_STATION_NAME))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Create coordinator based on data source
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, 600)
    data_source = entry.data.get(CONF_DATA_SOURCE, DATA_SOURCE_METEOSWISS)
    station_id = entry.data.get(CONF_STATION_ID)
    post_code = entry.data.get(CONF_POSTAL_CODE)

    if data_source == DATA_SOURCE_OPENMETEO:
        # Use Open-Meteo API for current weather AND forecast
        latitude = entry.data.get(CONF_LATITUDE, 47.05)
        longitude = entry.data.get(CONF_LONGITUDE, 8.31)

        coordinator = OpenMeteoDataUpdateCoordinator(
            hass,
            latitude=latitude,
            longitude=longitude,
            update_interval=update_interval,
        )
        _LOGGER.info("Using Open-Meteo API for lat=%s, lon=%s", latitude, longitude)

        # Forecast coordinator (also uses Open-Meteo)
        forecast_coordinator = MeteoSwissForecastCoordinator(
            hass,
            latitude=latitude,
            longitude=longitude,
            post_code=post_code,
            update_interval=3600,  # Forecast updates every hour
        )

    else:
        # Use MeteoSwiss API for current weather
        coordinator = MeteoSwissDataUpdateCoordinator(
            hass,
            station_id=station_id,
            update_interval=update_interval,
        )
        _LOGGER.info("Using MeteoSwiss API for station %s", station_id)

        # Load station coordinates for forecast (Open-Meteo)
        # IMPORTANT: Use station coordinates, not entry coordinates (user's location)
        lat, lon = await _load_station_coordinates(station_id)

        if lat is None or lon is None:
            _LOGGER.warning("Could not load station coordinates for forecast")
            # Fallback to entry coordinates
            lat = entry.data.get(CONF_LATITUDE)
            lon = entry.data.get(CONF_LONGITUDE)

        # Forecast coordinator (uses Open-Meteo with station coordinates)
        forecast_coordinator = MeteoSwissForecastCoordinator(
            hass,
            station_id=station_id,
            latitude=lat,
            longitude=lon,
            post_code=post_code,
            update_interval=3600,  # Forecast updates every hour
        )
        _LOGGER.info("Forecast coordinator using Open-Meteo with station coordinates: lat=%s, lon=%s", lat, lon)

    # Fetch initial data for current weather
    await coordinator.async_config_entry_first_refresh()

    # Fetch initial data for forecast
    await forecast_coordinator.async_config_entry_first_refresh()

    # Create alerts API and coordinator
    alerts_api = MeteoSwissAlertsAPI(session=None)
    alerts_api.postal_code = post_code

    from .binary_sensor import MeteoSwissAlertsCoordinator
    alerts_coordinator = MeteoSwissAlertsCoordinator(
        hass,
        alerts_api=alerts_api,
        update_interval=600,  # 10 minutes
    )

    # Create pollen API and coordinator
    from .pollen import MeteoSwissPollenAPI
    pollen_api = MeteoSwissPollenAPI(session=None)
    pollen_api.postal_code = post_code

    from .pollen_coordinator import MeteoSwissPollenCoordinator
    pollen_coordinator = MeteoSwissPollenCoordinator(
        hass,
        pollen_api=pollen_api,
        postal_code=post_code,
        update_interval=1800,  # 30 minutes
    )

    # Fetch initial alerts data
    await alerts_coordinator.async_config_entry_first_refresh()

    # Fetch initial pollen data
    await pollen_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["forecast_coordinator"] = forecast_coordinator
    hass.data[DOMAIN][entry.entry_id]["alerts_coordinator"] = alerts_coordinator
    hass.data[DOMAIN][entry.entry_id]["pollen_coordinator"] = pollen_coordinator
    hass.data[DOMAIN][entry.entry_id]["data_source"] = data_source
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
        # Close forecast coordinator session
        entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
        forecast_coordinator = entry_data.get("forecast_coordinator")
        if forecast_coordinator:
            await forecast_coordinator.async_close()

        # Close alerts coordinator
        alerts_coordinator = entry_data.get("alerts_coordinator")
        if alerts_coordinator:
            await alerts_coordinator.async_close()

        # Close pollen coordinator
        pollen_coordinator = entry_data.get("pollen_coordinator")
        if pollen_coordinator:
            await pollen_coordinator.async_close()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
