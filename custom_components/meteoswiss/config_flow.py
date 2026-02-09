"""Config flow for MeteoSwiss integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
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


class MeteoSwissConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MeteoSwiss."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_POSTAL_CODE): str,
                    }
                ),
                errors=errors,
            )

        # User entered postal code - show manual station selection
        _LOGGER.info("Postal code entered: %s", user_input[CONF_POSTAL_CODE])
        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID, default=""): str,
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

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle station selection step."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="station",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_STATION_ID, default=""): str,
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

        # Station entered - create entry
        station_id = user_input[CONF_STATION_ID]
        update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SEC)

        if not station_id:
            errors["base"] = "station_required"
            return self.async_show_form(
                step_id="station",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_STATION_ID, default=""): str,
                    }
                ),
                errors=errors,
            )

        # Create config entry
        _LOGGER.info("Creating entry for station: %s", station_id)
        return self.async_create_entry(
            title=f"MeteoSwiss {station_id}",
            data={
                CONF_POSTAL_CODE: user_input.get(CONF_POSTAL_CODE, ""),
                CONF_STATION_ID: station_id.lower(),
                CONF_STATION_NAME: station_id,
                CONF_UPDATE_INTERVAL: update_interval,
            },
        )
