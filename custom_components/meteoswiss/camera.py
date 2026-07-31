"""Camera platform for MeteoSwiss integration.

TODO: MeteoSwiss Regenradar (CombiPrecip) — no reliable public image URL found.

The following endpoints were tested and do NOT return usable radar images:
  - WMS geo.admin.ch with layer ch.meteoschweiz.ogc-radar-day → LayerNotDefined
  - MeteoSwiss clientlibs GIF URLs → 404
  - STAC API collections → no radar/precipitation dataset found
  - WMS GetCapabilities → no real-time precipitation layer

MeteoSwiss does not expose CombiPrecip radar images via a public,
undocumented API. The radar product is only available through:
  1. The MeteoSwiss app/website (JavaScript-rendered map tiles)
  2. Paid data products from MeteoSwiss

This file is a placeholder for when a reliable public API becomes available.

See: https://github.com/LNKtwo/ha-meteoswiss/issues for future updates.
"""
from __future__ import annotations

import logging

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import ATTRIBUTION, CONF_STATION_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up camera platform.

    TODO: Regenradar camera entity — currently disabled.
    No reliable public API for MeteoSwiss radar images found.
    """
    _LOGGER.debug(
        "Camera platform setup requested for %s — "
        "Regenradar not available (no public API)",
        entry.data.get(CONF_STATION_NAME),
    )
    # No entities to add until a reliable radar image API is found
    # async_add_entities([])


class MeteoSwissRadarCamera(Camera):
    """MeteoSwiss precipitation radar camera entity.

    TODO: Implement when a reliable public radar image API becomes available.
    """

    def __init__(self, entry: ConfigEntry, station_name: str) -> None:
        """Initialize camera."""
        super().__init__()
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_radar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="CombiPrecip Radar",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._attr_name = "Precipitation Radar"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return radar image bytes.

        TODO: Not implemented — no reliable public API for MeteoSwiss radar images.
        """
        return None
