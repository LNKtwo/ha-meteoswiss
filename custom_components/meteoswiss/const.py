"""Constants for meteoswiss integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "meteoswiss"
NAME: Final = "MeteoSwiss"
VERSION: Final = "4.0.4"

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
