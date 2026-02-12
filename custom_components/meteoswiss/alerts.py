"""MeteoSwiss Alerts Module using MeteoSwiss App API."""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# MeteoSwiss App API
METEOSWISS_APP_API_URL = "https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail"

# Warning types (from MeteoSwiss documentation)
WARN_TYPE_THUNDERSTORM = 1
WARN_TYPE_RAIN = 2
WARN_TYPE_SNOW = 3
WARN_TYPE_WIND = 4
WARN_TYPE_FOREST_FIRE = 10
WARN_TYPE_FLOOD = 11

# Warning levels
WARN_LEVEL_1 = 1  # No or minor danger
WARN_LEVEL_2 = 2  # Moderate danger
WARN_LEVEL_3 = 3  # Significant danger
WARN_LEVEL_4 = 4  # High danger
WARN_LEVEL_5 = 5  # Very high danger


@dataclass
class WeatherAlert:
    """Weather alert from MeteoSwiss."""

    alert_id: str
    warn_type: int
    warn_type_name: str
    warn_level: int
    warn_level_name: str
    title: str
    description: str
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    outlook: bool = False

    def is_active(self) -> bool:
        """Check if alert is currently active."""
        if self.outlook:
            return False  # Outlook is not an active alert

        if self.valid_to is None:
            return True  # No expiry date, assume active

        now = datetime.now()
        return self.valid_from <= now <= self.valid_to

    def is_critical(self) -> bool:
        """Check if alert is critical (level 3 or above)."""
        return self.warn_level >= WARN_LEVEL_3

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO strings
        if self.valid_from:
            data["valid_from"] = self.valid_from.isoformat()
        if self.valid_to:
            data["valid_to"] = self.valid_to.isoformat()
        return data

    def to_sensor_state(self) -> str:
        """Convert to sensor state."""
        if self.outlook:
            return "outlook"

        if self.is_active():
            if self.is_critical():
                return "critical"
            return "warning"

        return "clear"


class MeteoSwissAlertsAPI:
    """MeteoSwiss App API for weather warnings."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize."""
        self._session = session

    async def get_alerts(
        self,
        postal_code: str,
    ) -> list[WeatherAlert]:
        """Get weather alerts for a postal code.

        Args:
            postal_code: Swiss postal code (e.g., "8001")

        Returns:
            List of weather alerts
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            # Format PLZ: add "00" suffix (e.g., "8001" -> "800100")
            plz_formatted = f"{postal_code}00"

            url = f"{METEOSWISS_APP_API_URL}?plz={plz_formatted}"
            _LOGGER.info("Fetching alerts from: %s", url)

            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error("MeteoSwiss App API error: %s", response.status)
                    return []

                data = await response.json()

            alerts = self._parse_alerts(data, postal_code)
            _LOGGER.info("Found %d alerts for postal code %s", len(alerts), postal_code)

            return alerts

        except aiohttp.ClientError as err:
            _LOGGER.error("MeteoSwiss App API request failed: %s", err)
            return []
        except Exception as err:
            _LOGGER.error("Error fetching MeteoSwiss alerts: %s", err)
            return []

    def _parse_alerts(self, data: dict[str, Any], postal_code: str) -> list[WeatherAlert]:
        """Parse alerts from API response.

        The API returns data with optional 'warnings' field.
        The warnings field can be either a list (multiple alerts) or a dict (single alert).
        """
        alerts: list[WeatherAlert] = []

        # Check for warnings field
        if "warnings" not in data:
            _LOGGER.debug("No warnings field in response")
            return alerts

        warnings_data = data["warnings"]

        if not warnings_data:
            _LOGGER.debug("No warnings in response")
            return alerts

        # Handle both list and dict format
        if isinstance(warnings_data, list):
            # Multiple alerts
            for warning in warnings_data:
                if isinstance(warning, dict):
                    alert = self._parse_single_alert(warning, postal_code)
                    if alert:
                        alerts.append(alert)
        elif isinstance(warnings_data, dict):
            # Single alert
            alert = self._parse_single_alert(warnings_data, postal_code)
            if alert:
                alerts.append(alert)
        else:
            _LOGGER.warning("Unexpected warnings format: %s", type(warnings_data))

        return alerts

    def _parse_single_alert(self, warning_data: dict[str, Any], postal_code: str) -> WeatherAlert | None:
        """Parse a single alert from warning data.

        Args:
            warning_data: Single alert data (dict)
            postal_code: Postal code for alert ID generation

        Returns:
            WeatherAlert object or None if parsing fails
        """
        try:
            # Parse warning text (HTML or text format)
            warning_text = warning_data.get("text", "")
            html_text = warning_data.get("htmlText", "")

            # Parse warning level
            warn_level = warning_data.get("warnLevel", 0)

            # Parse warning type
            warn_type = warning_data.get("warnType", 0)

            # Parse valid from/to (Unix timestamps)
            valid_from_ts = warning_data.get("validFrom")
            valid_to_ts = warning_data.get("validTo")

            valid_from = None
            valid_to = None

            if valid_from_ts:
                try:
                    valid_from = datetime.fromtimestamp(valid_from_ts / 1000)
                except (ValueError, TypeError):
                    pass

            if valid_to_ts:
                try:
                    valid_to = datetime.fromtimestamp(valid_to_ts / 1000)
                except (ValueError, TypeError):
                    pass

            # Parse outlook flag
            outlook = warning_data.get("outlook", False)

            # Generate alert ID
            alert_id = f"{postal_code}_{warn_level}_{warn_type}_{valid_from_ts if valid_from_ts else 'now'}"

            # Create alert
            alert = WeatherAlert(
                alert_id=alert_id,
                warn_type=warn_type,
                warn_type_name=self._get_warn_type_name(warn_type),
                warn_level=warn_level,
                warn_level_name=self._get_warn_level_name(warn_level),
                title=f"{self._get_warn_type_name(warn_type)} - {self._get_warn_level_name(warn_level)}",
                description=warning_text,
                valid_from=valid_from,
                valid_to=valid_to,
                outlook=outlook,
            )

            return alert

        except Exception as err:
            _LOGGER.error("Error parsing alert: %s", err)
            return None

    @staticmethod
    def _get_warn_type_name(warn_type: int) -> str:
        """Get warning type name."""
        warn_type_names = {
            WARN_TYPE_THUNDERSTORM: "Thunderstorm",
            WARN_TYPE_RAIN: "Rain",
            WARN_TYPE_SNOW: "Snow",
            WARN_TYPE_WIND: "Wind",
            WARN_TYPE_FOREST_FIRE: "Forest Fire",
            WARN_TYPE_FLOOD: "Flood",
        }
        return warn_type_names.get(warn_type, f"Unknown ({warn_type})")

    @staticmethod
    def _get_warn_level_name(warn_level: int) -> str:
        """Get warning level name."""
        warn_level_names = {
            WARN_LEVEL_1: "Level 1 - No/minor danger",
            WARN_LEVEL_2: "Level 2 - Moderate danger",
            WARN_LEVEL_3: "Level 3 - Significant danger",
            WARN_LEVEL_4: "Level 4 - High danger",
            WARN_LEVEL_5: "Level 5 - Very high danger",
        }
        return warn_level_names.get(warn_level, f"Level {warn_level}")

    async def close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
