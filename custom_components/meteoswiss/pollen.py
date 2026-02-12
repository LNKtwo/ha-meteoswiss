"""Pollen integration based on Swiss Pollen data."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Pollen types
POLLEN_BIRCH = "birch"  # Birke
POLLEN_HAZEL = "hazel"  # Hasel
POLLEN_ALDER = "alder"  # Erle
POLLEN_GRASS = "grass"  # Gräser
POLLEN_RYE = "rye"  # Roggen
POLLEN_MUGWORT = "mugwort"  # Beifuß
POLLEN_AMBROSIA = "ambrosia"  # Ambrosia

# Pollen levels
POLLEN_LEVEL_NONE = 0
POLLEN_LEVEL_LOW = 1
POLLEN_LEVEL_MODERATE = 2
POLLEN_LEVEL_HIGH = 3
POLLEN_LEVEL_VERY_HIGH = 4

# Swiss Pollen API (from swiss-pollen project)
SWISS_POLLEN_STATIONS_URL = "https://www.meteoswiss.admin.ch/etc/climate/ambient/birch-pollen/forecast"


@dataclass
class PollenMeasurement:
    """Pollen measurement for a plant."""

    value: int | None = None
    level: int | None = None
    level_name: str | None = None
    timestamp: datetime | None = None

    def is_active(self) -> bool:
        """Check if pollen is currently active (value > 0)."""
        return self.value is not None and self.value > 0

    def is_high_risk(self) -> bool:
        """Check if pollen risk is high or very high."""
        return self.level is not None and self.level >= POLLEN_LEVEL_HIGH


class MeteoSwissPollenAPI:
    """MeteoSwiss Pollen API client."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize."""
        self._session = session
        self._cached_data: dict[str, Any] = {}

    async def get_pollen_data(
        self,
        postal_code: str,
    ) -> dict[str, PollenMeasurement]:
        """Get pollen data for a postal code.

        Args:
            postal_code: Swiss postal code (e.g., "8001")

        Returns:
            Dictionary of pollen measurements by plant type
        """
        # Check cache first
        cache_key = f"pollen:{postal_code}"
        if cache_key in self._cached_data:
            _LOGGER.debug("Using cached pollen data for %s", postal_code)
            return self._cached_data[cache_key]

        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            # Try different MeteoSwiss pollen forecast URLs
            # These are public URLs from MeteoSwiss
            pollen_urls = [
                f"https://www.meteoswiss.admin.ch/etc/climate/ambient/birch-pollen/forecast",
                f"https://www.meteoswiss.admin.ch/etc/climate/ambient/hazel-pollen/forecast",
                f"https://www.meteoswiss.admin.ch/etc/climate/ambient/alder-pollen/forecast",
                f"https://www.meteoswiss.admin.ch/etc/climate/ambient/ash-pollen/forecast",
                f"https://www.meteoswiss.admin.ch/etc/climate/ambient/grass-pollen/forecast",
                f"https://www.meteoswiss.admin.ch/etc/climate/ambient/ragweed-pollen/forecast",
            ]

            # Parse pollen data from MeteoSwiss pages
            pollen_data = {}

            for url in pollen_urls:
                try:
                    _LOGGER.debug("Fetching pollen from: %s", url)
                    async with self._session.get(url) as response:
                        if response.status != 200:
                            continue

                        text = await response.text()
                        measurement = self._parse_pollen_page(text, url)

                        if measurement and measurement.value is not None:
                            pollen_type = self._url_to_pollen_type(url)
                            if pollen_type:
                                pollen_data[pollen_type] = measurement

                except Exception as e:
                    _LOGGER.warning("Failed to fetch pollen from %s: %s", url, e)
                    continue

            # Cache results
            self._cached_data[cache_key] = pollen_data
            _LOGGER.info("Fetched pollen data for %s: %d types", postal_code, len(pollen_data))

            return pollen_data

        except aiohttp.ClientError as err:
            _LOGGER.error("Pollen API request failed: %s", err)
            return {}
        except Exception as err:
            _LOGGER.error("Error fetching pollen data: %s", err)
            return {}

    def _parse_pollen_page(self, text: str, url: str) -> PollenMeasurement | None:
        """Parse pollen data from MeteoSwiss HTML page.

        This is a simplified parser for demonstration.
        """
        try:
            # Look for pollen intensity values in the HTML
            # MeteoSwiss pages contain pollen level information
            # We'll extract the first numeric value that looks like a level

            import re

            # Search for patterns like "Level 1" or "Stufe 1" or similar
            # Also look for numerical values between 0-4 or 0-3

            # Try multiple patterns
            patterns = [
                r'(?:Stufe|Level|stufe|level)\s*[:=]\s*(\d)',
                r'pollen(?:_intensity)?[:=]\s*[\"\']?\s*(\d)\s*[\"\']?',
                r'intensity[:=]\s*[\"\']?\s*(\d)\s*[\"\']?',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    value_str = matches[0]
                    try:
                        value = int(value_str)
                        if 0 <= value <= 4:  # Valid pollen level
                            level = self._value_to_level(value)
                            timestamp = datetime.now()

                            return PollenMeasurement(
                                value=value,
                                level=level,
                                level_name=level,
                                timestamp=timestamp,
                            )
                    except ValueError:
                        pass

            _LOGGER.debug("Could not parse pollen level from page")
            return None

        except Exception as e:
            _LOGGER.error("Error parsing pollen page: %s", e)
            return None

    @staticmethod
    def _url_to_pollen_type(url: str) -> str | None:
        """Extract pollen type from URL."""
        if "birch" in url.lower():
            return POLLEN_BIRCH
        elif "hazel" in url.lower():
            return POLLEN_HAZEL
        elif "alder" in url.lower():
            return POLLEN_ALDER
        elif "ash" in url.lower():
            return POLLEN_ALDER
        elif "grass" in url.lower():
            return POLLEN_GRASS
        elif "ragweed" in url.lower():
            return POLLEN_AMBROSIA
        else:
            return None

    @staticmethod
    def _value_to_level(value: int) -> str:
        """Convert numeric value to level name."""
        if value == 0:
            return "None"
        elif value == 1:
            return "Low"
        elif value == 2:
            return "Moderate"
        elif value == 3:
            return "High"
        elif value == 4:
            return "Very High"
        else:
            return "Unknown"

    def clear_cache(self) -> None:
        """Clear pollen cache."""
        self._cached_data.clear()
        _LOGGER.debug("Pollen cache cleared")

    async def close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
