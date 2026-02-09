"""Config flow for MeteoSwiss integration."""
from __future__ import annotations

import asyncio
import csv
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_POSTAL_CODE
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_SEC,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
    STATIONS_METADATA_URL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POSTAL_CODE): str,
    }
)

STEP_STATION_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION_ID): str,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_SEC): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_UPDATE_INTERVAL),
        ),
    }
)


async def fetch_stations() -> list[dict[str, Any]]:
    """Fetch stations metadata from MeteoSwiss API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(STATIONS_METADATA_URL) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to fetch stations: {response.status}")

                content = await response.text()

        # Parse CSV - semicolon separated
        lines = content.strip().split("\n")

        if len(lines) < 2:
            return []

        # Parse header
        headers = [h.strip('"') for h in lines[0].split(";")]

        stations = []

        # Parse rows
        for line in lines[1:]:
            parts = line.split(";")
            if len(parts) >= 3:
                # Station ID is first column, Name is second
                station_id = parts[0].strip('"')
                station_name = parts[1].strip('"')

                # Canton is third column - filter for German-speaking cantons if needed
                canton = parts[2].strip('"')

                # Height is 8th column (index 7)
                try:
                    height = parts[7] if len(parts) > 7 else "N/A"
                except IndexError:
                    height = "N/A"

                if station_id and station_name:
                    stations.append(
                        {
                            "id": station_id.lower(),  # STAC API uses lowercase
                            "name": station_name,
                            "canton": canton,
                            "height": height,
                        }
                    )

        _LOGGER.info("Fetched %d stations", len(stations))
        return stations

    except Exception as err:
        _LOGGER.error("Error fetching stations: %s", err)
        return []


class MeteoSwissConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MeteoSwiss."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._postal_code: str | None = None
        self._stations: list[dict[str, Any]] = []
        self._selected_station: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._postal_code = user_input[CONF_POSTAL_CODE]

            # Fetch all stations
            try:
                self._stations = await fetch_stations()

                if not self._stations:
                    errors["base"] = "cannot_connect"
                else:
                    # For now, show all stations (can be improved with geocoding)
                    return await self.async_step_station()

            except Exception as err:
                _LOGGER.error("Error fetching stations: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle station selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._selected_station = next(
                (s for s in self._stations if s["id"] == user_input[CONF_STATION_ID]),
                None,
            )

            if self._selected_station:
                # Create config entry
                return self.async_create_entry(
                    title=f"MeteoSwiss {self._selected_station['name']}",
                    data={
                        CONF_POSTAL_CODE: self._postal_code,
                        CONF_STATION_ID: self._selected_station["id"],
                        CONF_STATION_NAME: self._selected_station["name"],
                        CONF_UPDATE_INTERVAL: user_input.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SEC
                        ),
                    },
                )

            errors["base"] = "station_not_found"

        # Prepare station options for UI
        station_options = {
            s["id"]: f"{s['name']} ({s['height']}m)" for s in self._stations
        }

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): vol.In(station_options),
                    vol.Optional(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL_SEC
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )
