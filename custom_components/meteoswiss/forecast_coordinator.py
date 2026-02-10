"""Forecast coordinator for MeteoSwiss ICON-CH2 data."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from aiohttp import TCPConnector

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

# MeteoSwiss CSV parameter IDs
PARAM_TEMPERATURE = "tre200s0"
PARAM_PRECIPITATION = "rre150z0"


class MeteoSwissForecastCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Class to manage fetching forecast data from MeteoSwiss ICON-CH2 API."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        update_interval: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.station_id = station_id.lower()
        self._session = session
        self._forecast_url = f"https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/{self.station_id}/ogd-smn_{self.station_id}_t_now.csv"

        super().__init__(
            hass,
            _LOGGER,
            name="meteoswiss_forecast",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch forecast data from CSV."""
        if self._session is None:
            self._session = aiohttp.ClientSession(connector=TCPConnector(ssl=False))

        try:
            _LOGGER.info("Fetching forecast CSV from: %s", self._forecast_url)
            async with self._session.get(self._forecast_url) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to download forecast CSV: %s", response.status)
                    raise UpdateFailed("Could not download forecast data")

                content = await response.text()

            # Parse CSV (semicolon-separated) manually
            lines = content.strip().split("\n")

            if len(lines) < 2:
                _LOGGER.error("Forecast CSV has no data lines")
                raise UpdateFailed("Forecast CSV is empty")

            # Parse header
            header_line = lines[0]
            headers = [h.strip() for h in header_line.split(";")]

            # Parse data rows (limit to 24 hours)
            forecast_data = []
            for line in lines[1:25]:  # Max 24 hours
                if line.strip():
                    values = [v.strip() for v in line.split(";")]
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(values):
                            row_dict[header] = values[i]

                    # Parse timestamp
                    timestamp_str = row_dict.get("reference_timestamp")
                    if timestamp_str:
                        try:
                            dt = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M")
                            row_dict["datetime"] = dt
                        except ValueError as e:
                            _LOGGER.warning("Could not parse timestamp %s: %s", timestamp_str, e)
                            continue

                    # Parse values
                    if PARAM_TEMPERATURE in row_dict and row_dict[PARAM_TEMPERATURE]:
                        try:
                            row_dict["temperature"] = float(row_dict[PARAM_TEMPERATURE])
                        except (ValueError, TypeError):
                            row_dict["temperature"] = None

                    if PARAM_PRECIPITATION in row_dict and row_dict[PARAM_PRECIPITATION]:
                        try:
                            row_dict["precipitation"] = float(row_dict[PARAM_PRECIPITATION])
                        except (ValueError, TypeError):
                            row_dict["precipitation"] = None

                    if row_dict:
                        forecast_data.append(row_dict)

            _LOGGER.info("Parsed %d forecast hours", len(forecast_data))
            return forecast_data

        except Exception as err:
            _LOGGER.error("Error parsing forecast CSV: %s", err)
            import traceback
            _LOGGER.error(traceback.format_exc())
            raise UpdateFailed(f"Failed to parse forecast data: {err}")

    async def async_close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
