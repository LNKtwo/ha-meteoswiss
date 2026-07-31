# MeteoSwiss Integration for Home Assistant

Swiss weather data directly from MeteoSwiss — current conditions, forecasts, alerts, and pollen data.

## Features

- **Current Weather** — Temperature, humidity, wind, pressure, precipitation, sunshine, global radiation, UV index
- **Weather Forecast** — Hourly and daily forecasts via Open-Meteo
- **Weather Alerts** — Official MeteoSwiss warnings (wind, rain, thunderstorm, snow, flood, forest fire)
- **Pollen Data** — Pollen levels via Open-Meteo Air Quality API
- **Smart Caching** — Intelligent TTL-based caching reduces API calls
- **Automatic Retry** — Exponential backoff on transient failures

## Installation

### HACS (recommended)

1. Add this repo as a Custom Repository in HACS
2. Search for "MeteoSwiss"
3. Install
4. Restart Home Assistant
5. Add the integration via Settings → Devices → Add Integration → MeteoSwiss

### Manual

1. Copy `custom_components/meteoswiss/` to your `custom_components/` directory
2. Restart Home Assistant
3. Add via Settings → Devices → Add Integration → MeteoSwiss

## Configuration

| Field | Description | Required |
|---|---|---|
| Station | MeteoSwiss weather station (e.g. LUC, GUT) | Yes (MeteoSwiss source) |
| Postal Code | Swiss postal code for alerts (e.g. 6048) | Yes |
| Data Source | `meteoswiss` (SwissMetNet) or `openmeteo` (Open-Meteo) | Yes |
| Latitude/Longitude | Used for Open-Meteo source | No (auto from station) |
| Update Interval | Refresh rate in seconds (min: 600) | No (default: 600) |

## Data Sources

### MeteoSwiss (default)
- Current conditions from SwissMetNet stations via `data.geo.admin.ch`
- 10-minute granularity measurements
- Official weather alerts via MeteoSwiss App API

### Open-Meteo (alternative)
- Current weather and forecasts via Open-Meteo API
- Useful if you're outside Switzerland or need different data

## Sensors

| Sensor | Unit | Source |
|---|---|---|
| Temperature | °C | MeteoSwiss |
| Humidity | % | MeteoSwiss |
| Wind Speed | km/h | MeteoSwiss |
| Wind Direction | ° | MeteoSwiss |
| Wind Gust | km/h | MeteoSwiss |
| Pressure | hPa | MeteoSwiss |
| Precipitation | mm | MeteoSwiss |
| Dew Point | °C | Calculated |
| Sunshine Duration | min | MeteoSwiss |
| Global Radiation | W/m² | MeteoSwiss |
| UV Index | UV | Open-Meteo |

## Requirements

- Home Assistant 2024.1 or newer
- Internet connection (cloud polling)

## License

MIT
