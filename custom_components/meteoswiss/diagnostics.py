"""Diagnostics support for MeteoSwiss."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
)

TO_REDACT = {
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
}

COORDINATORS = (
    "coordinator",
    "forecast_coordinator",
    "alerts_coordinator",
    "pollen_coordinator",
    "meteoswiss_pollen_coordinator",
)


def _summarize_data(data: Any) -> dict[str, Any]:
    """Return non-sensitive information about coordinator data."""
    if data is None:
        return {
            "type": "none",
            "item_count": 0,
        }

    if isinstance(data, dict):
        return {
            "type": "dict",
            "item_count": len(data),
            "keys": sorted(str(key) for key in data),
        }

    if isinstance(data, (list, tuple, set, frozenset)):
        return {
            "type": type(data).__name__,
            "item_count": len(data),
        }

    return {
        "type": type(data).__name__,
    }


def _coordinator_diagnostics(
    coordinator: DataUpdateCoordinator[Any],
) -> dict[str, Any]:
    """Return non-sensitive diagnostics for a coordinator."""
    update_interval = coordinator.update_interval

    diagnostics: dict[str, Any] = {
        "name": coordinator.name,
        "last_update_success": coordinator.last_update_success,
        "update_interval_seconds": (
            update_interval.total_seconds() if update_interval is not None else None
        ),
        "data": _summarize_data(coordinator.data),
    }

    if coordinator.last_exception is not None:
        diagnostics["last_exception"] = type(coordinator.last_exception).__name__

    data_source = getattr(coordinator, "data_source", None)
    if data_source is not None:
        diagnostics["data_source"] = data_source

    return diagnostics


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a MeteoSwiss config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]

    coordinators: dict[str, Any] = {}

    for key in COORDINATORS:
        coordinator = entry_data.get(key)
        if coordinator is None:
            coordinators[key] = {"available": False}
            continue

        coordinators[key] = {
            "available": True,
            **_coordinator_diagnostics(coordinator),
        }

    return {
        "config_entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "data_source": entry_data.get("data_source"),
        "coordinators": coordinators,
    }
