"""Forecast coordinator with Open-Meteo API (primary) + MeteoSwiss fallback."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from aiohttp import TCPConnector

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

# Open-Meteo API (always available)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# MeteoSwiss App API (fallback)
METEOSWISS_FORECAST_URL_TEMPLATE = "https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz={plz:06d}"
METEOSWISS_USER_AGENT = "android-31 ch.admin.meteoswiss-2160000"

# MeteoSwiss CSV parameter IDs
PARAM_TEMPERATURE = "tre200s0"
PARAM_PRECIPITATION = "rre150z0"


def _create_ssl_connector() -> TCPConnector:
    """Create a new SSL connector for each session to avoid reuse issues."""
    return TCPConnector(ssl=False)


class MeteoSwissForecastCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Class to manage fetching forecast data from Open-Meteo (primary) + MeteoSwiss (fallback)."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        post_code: str | None = None,
        update_interval: int = 3600,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self._station_id = station_id.lower() if station_id else None
        self._latitude = latitude
        self._longitude = longitude
        self._post_code = post_code
        self._session = session
        self._data_source = None  # Will track which API was used
        self._forecast_csv_url = (
            f"https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/{self._station_id}/ogd-smn_{self._station_id}_t_now.csv"
            if self._station_id
            else None
        )

        super().__init__(
            hass,
            _LOGGER,
            name="meteoswiss_forecast",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch forecast data from Open-Meteo (primary) or MeteoSwiss (fallback)."""

        # Try Open-Meteo first (always available)
        if self._latitude is not None and self._longitude is not None:
            try:
                data = await self._fetch_open_meteo_forecast()
                if data:
                    self._data_source = "open-meteo"
                    _LOGGER.info("Fetched forecast from Open-Meteo API")
                    return data
            except Exception as err:
                _LOGGER.warning("Open-Meteo API failed: %s, trying MeteoSwiss...", err)

        # Try MeteoSwiss CSV forecast
        if self._forecast_csv_url:
            try:
                data = await self._fetch_meteoswiss_csv_forecast()
                if data:
                    self._data_source = "meteoswiss-csv"
                    _LOGGER.info("Fetched forecast from MeteoSwiss CSV API")
                    return data
            except Exception as err:
                _LOGGER.warning("MeteoSwiss CSV failed: %s, trying MeteoSwiss App API...", err)

        # Try MeteoSwiss App API (as last resort)
        if self._post_code:
            try:
                data = await self._fetch_meteoswiss_app_forecast()
                if data:
                    self._data_source = "meteoswiss-app"
                    _LOGGER.info("Fetched forecast from MeteoSwiss App API")
                    return data
            except Exception as err:
                _LOGGER.error("MeteoSwiss App API failed: %s", err)

        # All APIs failed
        _LOGGER.error("All forecast APIs failed")
        raise UpdateFailed("Could not fetch forecast data from any source")

    async def _fetch_open_meteo_forecast(self) -> list[dict[str, Any]]:
        """Fetch forecast from Open-Meteo API."""
        if self._session is None:
            self._session = aiohttp.ClientSession(connector=_create_ssl_connector())

        url = (
            f"{OPEN_METEO_BASE_URL}"
            f"?latitude={self._latitude}"
            f"&longitude={self._longitude}"
            f"&hourly=temperature_2m,precipitation_probability,precipitation,windspeed_10m,winddirection_10m"
            f"&forecast_days=2"
            f"&timezone=Europe/Zurich"
        )

        _LOGGER.debug("Fetching from Open-Meteo: %s", url)

        async with self._session.get(url) as response:
            if response.status != 200:
                raise UpdateFailed(f"Open-Meteo API returned {response.status}")

            data = await response.json()

        forecast_data = []
        hourly = data.get("hourly", {})

        if not hourly:
            raise UpdateFailed("Open-Meteo API returned no hourly data")

        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        precip_prob = hourly.get("precipitation_probability", [])
        precip = hourly.get("precipitation", [])
        wind_speed = hourly.get("windspeed_10m", [])
        wind_dir = hourly.get("winddirection_10m", [])

        now = datetime.now(timezone.utc)
        start_idx = 0

        # Find starting index (next hour)
        for i, time_str in enumerate(times):
            try:
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                if dt >= now:
                    start_idx = i
                    break
            except ValueError:
                continue

        # Build forecast list (next 24 hours)
        for i in range(start_idx, min(start_idx + 24, len(times))):
            entry = {
                "datetime": times[i],
                "temperature": temps[i] if i < len(temps) else None,
                "precipitation_probability": precip_prob[i] if i < len(precip_prob) else None,
                "precipitation": precip[i] if i < len(precip) else None,
                "wind_speed": wind_speed[i] if i < len(wind_speed) else None,
                "wind_direction": wind_dir[i] if i < len(wind_dir) else None,
                "condition": self._map_open_meteo_condition(
                    precip_prob[i] if i < len(precip_prob) else None,
                    precip[i] if i < len(precip) else None,
                ),
            }
            forecast_data.append(entry)

        return forecast_data

    def _map_open_meteo_condition(self, precip_prob: float | None, precip: float | None) -> str:
        """Map Open-Meteo data to HA condition."""
        if precip and precip > 2.5:  # Heavy rain
            return "pouring"
        if precip and precip > 0:  # Rain
            return "rainy"
        if precip_prob and precip_prob > 60:  # Likely rain
            return "rainy"
        return "partlycloudy"  # Default

    async def _fetch_meteoswiss_csv_forecast(self) -> list[dict[str, Any]]:
        """Fetch forecast from MeteoSwiss CSV."""
        if self._session is None:
            self._session = aiohttp.ClientSession(connector=_create_ssl_connector())

        _LOGGER.info("Fetching forecast CSV from: %s", self._forecast_csv_url)

        async with self._session.get(self._forecast_csv_url) as response:
            if response.status != 200:
                raise UpdateFailed(f"MeteoSwiss CSV returned {response.status}")

            content = await response.text()

        # Parse CSV (semicolon-separated) manually
        lines = content.strip().split("\n")

        if len(lines) < 2:
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
                        row_dict["datetime"] = dt.isoformat()
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

                # Map CSV condition
                row_dict["condition"] = self._map_csv_condition(row_dict.get("precipitation"))

                if row_dict:
                    forecast_data.append(row_dict)

        return forecast_data

    def _map_csv_condition(self, precip: float | None) -> str:
        """Map CSV precipitation to HA condition."""
        if precip and precip > 0:
            return "rainy"
        return "partlycloudy"

    async def _fetch_meteoswiss_app_forecast(self) -> list[dict[str, Any]]:
        """Fetch forecast from MeteoSwiss App API (fallback)."""
        if self._session is None:
            self._session = aiohttp.ClientSession(connector=_create_ssl_connector())

        if not self._post_code:
            raise UpdateFailed("No postal code configured")

        url = METEOSWISS_FORECAST_URL_TEMPLATE.format(plz=int(self._post_code))
        _LOGGER.info("Fetching from MeteoSwiss App API: %s", url)

        async with self._session.get(
            url,
            headers={
                "User-Agent": METEOSWISS_USER_AGENT,
                "Accept-Language": "de",
                "Accept": "application/json",
            },
        ) as response:
            if response.status != 200:
                raise UpdateFailed(f"MeteoSwiss App API returned {response.status}")

            data = await response.json()

        if data.get("error"):
            raise UpdateFailed(f"MeteoSwiss App API error: {data.get('error')}")

        # Parse forecast from JSON
        forecast_data = []
        graph = data.get("graph", {})
        forecast = data.get("forecast", [])

        # Use hourly forecast from graph if available
        start_timestamp = graph.get("start")
        temp_max_1h = graph.get("temperatureMax1h", [])
        temp_mean_1h = graph.get("temperatureMean1h", [])
        precip_1h = graph.get("precipitation1h", [])
        precip_prob_3h = graph.get("precipitationProbability3h", [])
        weather_icon_3h = graph.get("weatherIcon3h", [])

        if start_timestamp:
            now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            start = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
            offset = int((now - start).total_seconds() / 3600) if now > start else 0

            # Expand 3-hourly data to hourly
            from itertools import chain, repeat

            expanded_icons = list(chain.from_iterable(repeat(x, 3) for x in weather_icon_3h))
            expanded_precip_prob = list(chain.from_iterable(repeat(x, 3) for x in precip_prob_3h))

            for i in range(offset, min(offset + 24, len(temp_mean_1h))):
                entry = {
                    "datetime": (start + timedelta(hours=i)).isoformat(),
                    "temperature": temp_mean_1h[i] if i < len(temp_mean_1h) else None,
                    "precipitation": precip_1h[i] if i < len(precip_1h) else None,
                    "precipitation_probability": expanded_precip_prob[i] if i < len(expanded_precip_prob) else None,
                    "condition": self._map_meteoswiss_icon(expanded_icons[i] if i < len(expanded_icons) else None),
                }
                forecast_data.append(entry)

        elif forecast:
            # Fallback to daily forecast
            for day in forecast[:2]:  # Next 2 days
                date_str = day.get("dayDate")
                if date_str:
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        # Create hourly entries for the day (simplified)
                        for hour in range(24):
                            entry = {
                                "datetime": (dt + timedelta(hours=hour)).isoformat(),
                                "temperature": day.get("temperatureMax") if hour < 12 else day.get("temperatureMin"),
                                "precipitation": day.get("precipitation"),
                                "condition": self._map_meteoswiss_icon(day.get("iconDay")),
                            }
                            forecast_data.append(entry)
                    except ValueError:
                        continue

        return forecast_data

    def _map_meteoswiss_icon(self, icon: int | None) -> str:
        """Map MeteoSwiss icon to HA condition."""
        if icon is None:
            return "partlycloudy"

        # MeteoSwiss icon mapping (simplified)
        icon_map = {
            1: "sunny",  # Clear
            2: "partlycloudy",  # Partly cloudy
            3: "partlycloudy",
            4: "cloudy",
            5: "cloudy",
            6: "rainy",  # Rain
            20: "pouring",  # Heavy rain
            8: "snowy",  # Snow
            12: "lightning",  # Thunder
        }

        return icon_map.get(icon, "partlycloudy")

    @property
    def data_source(self) -> str | None:
        """Return which API was used to fetch data."""
        return self._data_source

    async def async_close(self) -> None:
        """Close aiohttp session."""
        if self._session is not None:
            await self._session.close()
            self._session = None
