# MeteoSwiss Integration for Home Assistant

[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/LNKtwo/ha-meteoswiss)
[![version](https://img.shields.io/badge/version-6.0.1-blue.svg)](https://github.com/LNKtwo/ha-meteoswiss/releases)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Swiss weather data directly from **MeteoSwiss** — current conditions, forecasts, official weather alerts, and pollen data for Home Assistant.

## Features

| Feature | Source | Description |
|---|---|---|
| 🌡️ **Current Weather** | MeteoSwiss SwissMetNet | Temperature, humidity, wind, pressure, precipitation, sunshine, global radiation |
| ⛅ **Weather Forecast** | Open-Meteo | Hourly and daily forecasts with condition mapping |
| ⚠️ **Weather Alerts** | MeteoSwiss | Official warnings: wind, rain, thunderstorm, snow, flood, forest fire |
| 🌸 **Pollen Data** | Open-Meteo AQI | Pollen levels for alder, birch, grass, olive, mugwort, and ragweed |
| 🔁 **Smart Caching** | Internal | TTL-based caching reduces API calls |
| 🛡️ **Auto-Retry** | Internal | Exponential backoff on transient failures |

## Installation

### HACS (recommended)

1. Go to **HACS** → **Integrations** → ⋮ → **Custom Repositories**
2. Add `https://github.com/LNKtwo/ha-meteoswiss` as category **Integration**
3. Search for **MeteoSwiss** → **Install**
4. Restart Home Assistant
5. **Settings** → **Devices** → **Add Integration** → search **MeteoSwiss**

### Manual

1. Download and copy the `custom_components/meteoswiss/` folder to your HA `custom_components/` directory
2. Restart Home Assistant
3. **Settings** → **Devices** → **Add Integration** → search **MeteoSwiss**

## Configuration

The integration is configured via Home Assistant's UI:

| Field | Description | Required | Default |
|---|---|---|---|
| **Station** | MeteoSwiss station code (e.g. `LUC` for Lucerne) | Yes | — |
| **Postal Code** | Swiss postal code for weather alerts (e.g. `6048`) | Yes | — |
| **Data Source** | `meteoswiss` (SwissMetNet) or `openmeteo` (Open-Meteo) | Yes | `meteoswiss` |
| **Update Interval** | Refresh interval in seconds | No | `600` (10 min) |

### Finding Your Station

SwissMetNet stations: [MeteoSwiss Station Map](https://www.meteoswiss.admin.ch/weather/measurement-values.html)

Common stations:

| Code | Location |
|---|---|
| `LUC` | Lucerne |
| `ZRH` | Zurich |
| `BER` | Bern |
| `BSL` | Basel |
| `GVE` | Geneva |
| `LUG` | Lugano |

## Sensors

### Current Weather

| Sensor | Unit | Device Class |
|---|---|---|
| Temperature | °C | Temperature |
| Humidity | % | Humidity |
| Wind Speed | km/h | Wind Speed |
| Wind Direction | ° | — |
| Wind Gust | km/h | Wind Speed |
| Pressure | hPa | Pressure |
| Precipitation | mm | Precipitation |
| Dew Point | °C | Temperature |
| Sunshine Duration | min | Duration |
| Global Radiation | W/m² | Irradiance |
| UV Index | UV Index | — |

### Weather Alerts

Binary sensors for active weather warnings with severity levels and alert details as attributes.

### Pollen

Pollen concentration sensors for major allergen types.

## Requirements

- Home Assistant **2024.7** or newer
- Internet connection (cloud polling)

## Data Sources

### MeteoSwiss (default)
- **Current conditions** from SwissMetNet stations via `data.geo.admin.ch` STAC API
- **Weather alerts** via MeteoSwiss App API
- 10-minute measurement granularity

### Open-Meteo (alternative)
- Current weather and forecasts via Open-Meteo API
- Useful outside Switzerland or for different data needs

## Support

- **Issues:** [GitHub Issues](https://github.com/LNKtwo/ha-meteoswiss/issues)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

## License

[MIT](LICENSE)

---

*Data source: [MeteoSwiss](https://www.meteoswiss.admin.ch/) · Forecast: [Open-Meteo](https://open-meteo.com/)*
