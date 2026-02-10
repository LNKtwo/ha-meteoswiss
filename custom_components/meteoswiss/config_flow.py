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

# SSL connector for systems with outdated certificates
# This is a fallback for systems that cannot update CA certificates
_SSL_CONNECTOR = TCPConnector(ssl=False)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POSTAL_CODE): str,
        vol.Optional(CONF_STATION_ID, default=""): str,
    }
)

        # This schema will be built dynamically with available stations
STEP_STATION_DATA_SCHEMA = vol.Schema({
            vol.Required(CONF_POSTAL_CODE): str,
            vol.Optional(CONF_STATION_ID, default=""): str,
        })


class MeteoSwissConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for meteoswiss."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._post_code: str | None = None
        self._stations: list[dict[str, Any]] = []

    async def _load_stations(self) -> list[dict[str, Any]]:
        """Load stations metadata from CSV."""
        if self._stations:
            return self._stations

        try:
            async with aiohttp.ClientSession(connector=_SSL_CONNECTOR) as session:
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

            self._stations = sorted(stations, key=lambda x: x["name"])
            _LOGGER.info("Loaded %d stations", len(stations))

            return self._stations

        except Exception as err:
            _LOGGER.error("Error loading stations: %s", err)
            return []

    async def _find_nearest_station(self, postal_code: str) -> dict[str, Any] | None:
        """Find nearest station by postal code (Swiss coordinates approximation)."""
        stations = await self._load_stations()
        if not stations:
            return None

        # Approximate Swiss coordinates for postal codes
        # This is a simplified mapping - for production, use a proper geocoding API
        postal_code = postal_code.zfill(4)

        # Quick Canton lookup from first 2 digits of postal code
        canton_map = {
            "80": "ZH", "81": "ZH", "82": "ZH", "83": "ZH", "84": "ZH", "85": "ZH",
            "30": "BE", "32": "BE", "33": "BE", "34": "BE", "35": "BE", "36": "BE",
            "40": "BS", "41": "BS", "42": "BL", "43": "BL", "44": "BL", "45": "BL",
            "50": "SO", "51": "SO", "52": "SO", "53": "SO", "57": "SO",
            "60": "LU", "61": "LU", "62": "LU", "63": "LU", "64": "LU",
            "70": "AG", "71": "AG", "72": "AG", "73": "AG", "74": "AG", "75": "AG",
            "90": "SG", "91": "SG", "92": "SG", "93": "SG", "94": "SG", "95": "SG",
            "10": "VD", "11": "VD", "12": "VD", "13": "VD", "14": "VD", "15": "VD",
            "20": "NE", "23": "JU", "25": "JU",
            "39": "VS", "19": "VS",
            "27": "FR", "17": "FR",
            "26": "JU",
            "28": "GR",
            "66": "UR", "67": "SZ", "88": "SZ", "87": "SZ",
            "82": "GL", "86": "GL",
            "77": "NW", "60": "OW",
            "65": "TG", "85": "TG",
            "94": "AI", "94": "AR",
        }

        canton = canton_map.get(postal_code[:2])

        # Filter by canton first
        canton_stations = [s for s in stations if s["canton"] == canton] if canton else []

        # If no canton match or empty, use all stations
        target_stations = canton_stations if canton_stations else stations

        # Return first matching station (can be improved with distance calculation)
        return target_stations[0] if target_stations else stations[0]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial step."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        self._post_code = user_input[CONF_POSTAL_CODE]
        _LOGGER.info("Postal code entered: %s", self._post_code)

        return await self.async_step_station()

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle station selection step."""
        errors: dict[str, str] = {}

        # Load stations
        stations = await self._load_stations()
        if not stations:
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="station",
                data_schema=vol.Schema({
                    vol.Required(CONF_STATION_ID, default=""): str,
                }),
                errors=errors,
            )

        # Find nearest station as default
        nearest = await self._find_nearest_station(self._post_code or "")
        default_station = nearest["id"] if nearest else stations[0]["id"]

        if user_input is None:
            # Build dynamic schema with station selector
            station_options = {s["id"]: s["label"] for s in stations}

            schema = vol.Schema({
                vol.Required(CONF_STATION_ID, default=default_station): vol.In(station_options),
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_SEC): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL),
                ),
            })

            return self.async_show_form(
                step_id="station",
                data_schema=schema,
                errors=errors,
            )

        station_id = user_input[CONF_STATION_ID]
        update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SEC)

        # Find station name
        station = next((s for s in stations if s["id"] == station_id), None)
        station_name = station["name"] if station else station_id

        # Create config entry
        _LOGGER.info("Creating entry for station: %s", station_id)
        return self.async_create_entry(
            title=f"MeteoSwiss {station_name} ({station_id.upper()})",
            data={
                CONF_POSTAL_CODE: self._post_code,
                CONF_STATION_ID: station_id.lower(),
                CONF_STATION_NAME: station_name,
                CONF_UPDATE_INTERVAL: update_interval,
            },
        )
