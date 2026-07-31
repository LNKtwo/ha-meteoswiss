"""Pollen data coordinator using MeteoSwiss measured pollen data (ogd-pollen).

Fetches measured pollen concentrations from MeteoSwiss pollen stations
via the data.geo.admin.ch STAC API (ch.meteoschweiz.ogd-pollen).

16 stations across Switzerland provide hourly measured concentrations for:
  - Birch (Birke / Betula)
  - Alder (Erle / Alnus)
  - Hazel (Hasel / Corylus)
  - Beech (Buche / Fagus)
  - Common ash (Esche / Fraxinus)
  - Oak (Eiche / Quercus)
  - Grasses (Gräser / Poaceae)
  - Mugwort (Beifuss / Artemisia)
  - Ragweed (Ambrosia / Ambrosia)
  - Elm (Ulme / Ulmus)
  - Nettle (Nessel / Urtica)
  - Plantain (Wegerich / Plantago)
  - Sorrel (Sauerampfer / Rumex)

Data source: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# STAC API for pollen collection
POLLEN_STAC_COLLECTION_URL = (
    "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen"
)
POLLEN_DATA_BASE_URL = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen"
)

# Pollen parameter codes (MeteoSwiss naming convention)
# Format: ka{genus_abbrev}{time_resolution}{version}
POLLEN_PARAM_MAP: dict[str, str] = {
    # Common allergens → API column names (hourly data)
    "birch": "kabetuh0",       # Birke / Betula
    "alder": "kaalnuh0",       # Erle / Alnus
    "hazel": "kacoryh0",       # Hasel / Corylus
    "beech": "kafaguh0",       # Buche / Fagus
    "ash": "kafraxh0",         # Esche / Fraxinus
    "oak": "kaqueth0",         # Eiche / Quercus (if available)
    "grass": "khpoach0",       # Gräser / Poaceae
    "mugwort": "kaartuh0",     # Beifuss / Artemisia (if available)
    "ragweed": "kaambh0",      # Ambrosia (if available)
}

# All pollen types we track (matching the data columns actually present)
POLLEN_TRACKED = [
    "birch",
    "alder",
    "hazel",
    "beech",
    "ash",
    "grass",
]

# Mapping from our key → MeteoSwiss column name
# These are the columns typically present in the _h_now.csv files
POLLEN_CSV_COLUMNS: dict[str, str] = {
    "birch": "kabetuh0",
    "alder": "kaalnuh0",
    "hazel": "kacoryh0",
    "beech": "kafaguh0",
    "ash": "kafraxh0",
    "grass": "khpoach0",
}


class MeteoSwissPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching measured pollen data from MeteoSwiss."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str = "PBE",
        update_interval: int = 3600,  # 1 hour default
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self._station_id = station_id.lower()
        self._session = session

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_pollen_meteoswiss",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch pollen data from MeteoSwiss ogd-pollen."""
        if self._session is None:
            raise RuntimeError("No aiohttp session provided to MeteoSwissPollenCoordinator")

        _LOGGER.debug("Fetching MeteoSwiss pollen data for station %s", self._station_id)

        # Build URL for hourly "now" CSV
        url = f"{POLLEN_DATA_BASE_URL}/{self._station_id}/ogd-pollen_{self._station_id}_h_now.csv"

        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "MeteoSwiss pollen API returned %s for station %s",
                        response.status,
                        self._station_id,
                    )
                    return {}

                content = await response.text()

            data = self._parse_csv(content)

            if not data:
                _LOGGER.warning("No pollen data parsed for station %s", self._station_id)
                return {}

            _LOGGER.debug(
                "Successfully parsed pollen data for station %s: %d pollen types",
                self._station_id,
                sum(1 for k, v in data.items() if isinstance(v, dict) and v.get("current") is not None),
            )
            return data

        except aiohttp.ClientError as err:
            _LOGGER.error("MeteoSwiss pollen API request failed: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Error fetching MeteoSwiss pollen data: %s", err)
            return {}

    def _parse_csv(self, csv_text: str) -> dict[str, Any]:
        """Parse MeteoSwiss pollen CSV data.

        The CSV has semicolon-separated columns:
        station_abbr;reference_timestamp;kabetuh0;khpoach0;kaalnuh0;kacoryh0;kafaguh0;kafraxh0;kaquerh0

        Each row is an hourly measurement.
        """
        result: dict[str, Any] = {
            "station_id": self._station_id.upper(),
            "last_update": None,
            "source": "MeteoSwiss ogd-pollen",
        }

        try:
            # Parse CSV with proper handling
            reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")

            if reader.fieldnames is None:
                _LOGGER.error("No header row in pollen CSV")
                return {}

            _LOGGER.debug("Pollen CSV columns: %s", reader.fieldnames)

            # Read all rows, keep the latest (last) one
            rows = list(reader)
            if not rows:
                _LOGGER.warning("No data rows in pollen CSV")
                return {}

            latest = rows[-1]
            timestamp = latest.get("reference_timestamp", "")
            result["last_update"] = timestamp

            # Parse each pollen type
            for pollen_key, csv_column in POLLEN_CSV_COLUMNS.items():
                if csv_column not in latest:
                    _LOGGER.debug("Column %s not found in pollen CSV", csv_column)
                    result[pollen_key] = {
                        "current": None,
                        "unit": "No/m³",
                        "source": "MeteoSwiss measured",
                    }
                    continue

                raw_value = latest.get(csv_column, "")
                try:
                    value = int(raw_value) if raw_value else None
                except ValueError:
                    value = None

                # Also extract last 24h history
                history_24h = []
                for row in rows[-24:]:
                    hist_raw = row.get(csv_column, "")
                    try:
                        hist_val = int(hist_raw) if hist_raw else None
                    except ValueError:
                        hist_val = None
                    history_24h.append(hist_val)

                result[pollen_key] = {
                    "current": value,
                    "unit": "No/m³",
                    "source": "MeteoSwiss measured",
                    "history_24h": history_24h,
                }

        except Exception as err:
            _LOGGER.error("Error parsing pollen CSV: %s", err)
            return {}

        return result
