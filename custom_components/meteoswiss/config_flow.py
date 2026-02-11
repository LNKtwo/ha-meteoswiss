"""Config flow for meteoswiss integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from aiohttp import TCPConnector

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_SEC,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
    STATIONS_METADATA_URL,
)

_LOGGER = logging.getLogger(__name__)

def _create_ssl_connector() -> TCPConnector:
    """Create a new SSL connector for each session to avoid reuse issues."""
    return TCPConnector(ssl=False)


class MeteoSwissConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for meteoswiss."""

    VERSION = 1

    async def _load_stations(self) -> list[dict[str, Any]]:
        """Load stations metadata from CSV."""
        try:
            async with aiohttp.ClientSession(connector=_create_ssl_connector()) as session:
                async with session.get(STATIONS_METADATA_URL) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to load stations: %s", response.status)
                        return []

                    content_bytes = await response.read()

            # Try different encodings for CSV (MeteoSwiss uses ISO-8859-1 with umlauts)
            lines = None
            for encoding in ['iso-8859-1', 'latin-1', 'cp1252', 'utf-8-sig', 'utf-8']:
                try:
                    decoded = content_bytes.decode(encoding)
                    lines = decoded.strip().split("\n")
                    if len(lines) > 10:  # Check if we got valid data
                        _LOGGER.info("Successfully decoded CSV with encoding: %s", encoding)
                        break
                except UnicodeDecodeError:
                    continue
            
            if not lines or len(lines) < 2:
                _LOGGER.error("Failed to decode CSV with any encoding")
                return []

            # Parse CSV (semicolon-separated)
            stations = []
            for line in lines[1:]:  # Skip header
                parts = line.split(";")
                if len(parts) >= 3:
                    station_id = parts[0].strip().lower()
                    station_name = parts[1].strip()
                    canton = parts[2].strip()

                    # Extract coordinates (WGS84)
                    lat = float(parts[14]) if len(parts) > 14 and parts[14] else None
                    lon = float(parts[15]) if len(parts) > 15 and parts[15] else None

                    if station_id and station_id != "station_abbr":
                        stations.append({
                            "id": station_id,
                            "name": station_name,
                            "canton": canton,
                            "label": f"{station_name} ({station_id.upper()})",
                            "lat": lat,
                            "lon": lon,
                        })

            stations = sorted(stations, key=lambda x: x["name"])
            _LOGGER.info("Loaded %d stations", len(stations))

            return stations

        except Exception as err:
            _LOGGER.error("Error loading stations: %s", err)
            return []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial step - combined PLZ and station selection."""
        errors: dict[str, str] = {}

        if user_input is None:
            # Load stations for dropdown
            stations = await self._load_stations()
            station_options = {s["id"]: s["label"] for s in stations}

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required(CONF_POSTAL_CODE): str,
                    vol.Required(CONF_STATION_ID, default=""): vol.In(station_options),
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_SEC): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL),
                    ),
                }),
                errors=errors,
            )

        # Process form submission
        post_code = user_input[CONF_POSTAL_CODE]
        station_id = user_input[CONF_STATION_ID]
        update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SEC)

        # Find station details
        stations = await self._load_stations()
        station = next((s for s in stations if s["id"] == station_id), None)
        station_name = station["name"] if station else station_id
        lat = station["lat"] if station else None
        lon = station["lon"] if station else None

        # Create config entry
        _LOGGER.info("Creating entry for station: %s (lat=%s, lon=%s)", station_id, lat, lon)
        return self.async_create_entry(
            title=f"MeteoSwiss {station_name} ({station_id.upper()})",
            data={
                CONF_POSTAL_CODE: post_code,
                CONF_STATION_ID: station_id.lower(),
                CONF_STATION_NAME: station_name,
                CONF_LATITUDE: lat,
                CONF_LONGITUDE: lon,
                CONF_UPDATE_INTERVAL: update_interval,
            },
        )
