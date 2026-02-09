"""Config flow for meteoswiss integration."""
from __future__ import annotations

import logging
from typing import Any

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


class MeteoSwissConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for meteoswiss."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._post_code: str | None = None

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

        if user_input is None:
            return self.async_show_form(
                step_id="station",
                data_schema=STEP_STATION_DATA_SCHEMA,
                errors=errors,
            )

        station_id = user_input[CONF_STATION_ID]
        update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SEC)

        if not station_id:
            errors["base"] = "station_required"
            return self.async_show_form(
                step_id="station",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_STATION_ID): str,
                    }
                ),
                errors=errors,
            )

        # Create config entry (manual station selection for now)
        _LOGGER.info("Creating entry for station: %s", station_id)
        return self.async_create_entry(
            title=f"MeteoSwiss {station_id}",
            data={
                CONF_POSTAL_CODE: self._post_code,
                CONF_STATION_ID: station_id.lower(),
                CONF_STATION_NAME: station_id,
                CONF_UPDATE_INTERVAL: update_interval,
            },
        )
