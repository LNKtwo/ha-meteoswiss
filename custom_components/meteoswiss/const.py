"""Constants for meteoswiss integration."""

from __future__ import annotations

from typing import Final

import aiohttp

from aiohttp import TCPConnector

DOMAIN: Final = "meteoswiss"
NAME: Final = "MeteoSwiss"

# API URLs
API_BASE: Final = "https://data.geo.admin.ch/api/stac/v1"
STAC_COLLECTION: Final = "ch.meteoschweiz.ogd-smn"
STATIONS_METADATA_URL: Final = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv"
)
PARAMETERS_METADATA_URL: Final = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_parameters.csv"
)

# Data granularity (t=10min, h=hourly, d=daily)
GRANULARITY_10MIN: Final = "t"
GRANULARITY_HOURLY: Final = "h"
GRANULARITY_DAILY: Final = "d"

# Update frequency (seconds)
DEFAULT_UPDATE_INTERVAL: Final = 600  # 10 minutes
MIN_UPDATE_INTERVAL: Final = 600

# Config keys
CONF_POSTAL_CODE: Final = "postal_code"
CONF_POSTCODE: Final = "postal_code"  # Alias for compatibility
CONF_STATION_ID: Final = "station_id"
CONF_STATION_NAME: Final = "station_name"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_POLLEN_STATION_CODE: Final = "polen_station_code"
CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"
CONF_DATA_SOURCE: Final = "data_source"

# Data sources
DATA_SOURCE_METEOSWISS: Final = "meteoswiss"
DATA_SOURCE_OPENMETEO: Final = "openmeteo"

# Defaults
DEFAULT_UPDATE_INTERVAL_SEC: Final = 600

# Sensor types
SENSOR_TEMPERATURE: Final = "temperature"
SENSOR_HUMIDITY: Final = "humidity"
SENSOR_WIND_SPEED: Final = "wind_speed"
SENSOR_WIND_DIRECTION: Final = "wind_direction"
SENSOR_PRECIPITATION: Final = "precipitation"
SENSOR_PRESSURE: Final = "pressure"
SENSOR_WIND_GUST: Final = "wind_gust"
SENSOR_DEW_POINT: Final = "dew_point"
SENSOR_SUNSHINE: Final = "sunshine_duration"
SENSOR_GLOBAL_RADIATION: Final = "global_radiation"
SENSOR_UV_INDEX: Final = "uv_index"

# Condition mapping
CONDITION_CLEAR = "clear-night"
CONDITION_CLOUDY = "cloudy"
CONDITION_FOG = "fog"
CONDITION_PARTLY_CLOUDY = "partly-cloudy"
CONDITION_RAIN = "rainy"
CONDITION_SNOW = "snowy"
CONDITION_SUNNY = "sunny"

# Source attribution
ATTRIBUTION: Final = "Source: MeteoSwiss"

# API timeout (30 seconds for all requests)
DEFAULT_API_TIMEOUT: Final = aiohttp.ClientTimeout(total=30)

# WMO weather code → HA condition mapping (used by weather.py, forecast_coordinator.py, openmeteo_coordinator.py)
WMO_WEATHER_CODES: Final[dict[int, str]] = {
    0: "sunny", 1: "sunny", 2: "partlycloudy", 3: "cloudy",
    45: "fog", 48: "fog",
    51: "rainy", 53: "rainy", 55: "rainy", 56: "rainy", 57: "rainy",
    61: "rainy", 63: "rainy", 65: "rainy", 66: "rainy", 67: "rainy",
    71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy",
    80: "rainy", 81: "rainy", 82: "rainy", 85: "snowy", 86: "snowy",
    95: "lightning", 96: "lightning", 99: "lightning",
}


# Session utilities
def _create_ssl_connector() -> TCPConnector:
    """Create a new SSL connector for aiohttp sessions.

    SSL is enabled. Previously disabled for systems with outdated certificates,
    but both data.geo.admin.ch and api.open-meteo.com have valid certs.
    """
    return TCPConnector(ssl=True)
