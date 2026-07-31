"""Diagnostics platform for MeteoSwiss integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Keys whose values should be redacted in diagnostics output
TO_REDACT: frozenset[str] = frozenset(
    {
        "postal_code",
    }
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})

    diagnostics_data: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
            "version": entry.version,
        },
        "data_source": entry_data.get("data_source"),
    }

    # Coordinator data (current weather)
    coordinator = entry_data.get("coordinator")
    if coordinator:
        diagnostics_data["coordinator"] = {
            "last_update_success": coordinator.last_update_success,
            "last_exception": str(coordinator.last_exception) if coordinator.last_exception else None,
            "update_interval": str(coordinator.update_interval),
            "data": coordinator.data if coordinator.data else None,
        }

    # Forecast coordinator data
    forecast_coordinator = entry_data.get("forecast_coordinator")
    if forecast_coordinator:
        forecast_data = forecast_coordinator.data or []
        diagnostics_data["forecast_coordinator"] = {
            "last_update_success": forecast_coordinator.last_update_success,
            "last_exception": str(forecast_coordinator.last_exception) if forecast_coordinator.last_exception else None,
            "update_interval": str(forecast_coordinator.update_interval),
            "forecast_entries": len(forecast_data),
            "data": forecast_data[:5] if forecast_data else None,  # First 5 entries as sample
        }

    # Pollen / Air Quality coordinator data
    pollen_coordinator = entry_data.get("pollen_coordinator")
    if pollen_coordinator:
        diagnostics_data["pollen_coordinator"] = {
            "last_update_success": pollen_coordinator.last_update_success,
            "last_exception": str(pollen_coordinator.last_exception) if pollen_coordinator.last_exception else None,
            "update_interval": str(pollen_coordinator.update_interval),
            "data": pollen_coordinator.data if pollen_coordinator.data else None,
        }

    # Alerts coordinator data
    alerts_coordinator = entry_data.get("alerts_coordinator")
    if alerts_coordinator:
        alerts_data = alerts_coordinator.data or []
        diagnostics_data["alerts_coordinator"] = {
            "last_update_success": alerts_coordinator.last_update_success,
            "last_exception": str(alerts_coordinator.last_exception) if alerts_coordinator.last_exception else None,
            "alerts_count": len(alerts_data),
            "data": [str(a) for a in alerts_data[:3]] if alerts_data else None,
        }

    return diagnostics_data
