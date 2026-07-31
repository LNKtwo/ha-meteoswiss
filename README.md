# 🇨🇭 MeteoSwiss for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/LNKtwo/ha-meteoswiss)
[![Version](https://img.shields.io/badge/version-8.0.0-blue.svg)](https://github.com/LNKtwo/ha-meteoswiss/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![HA Min Version](https://img.shields.io/badge/HA-2024.7%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Downloads](https://img.shields.io/github/downloads/LNKtwo/ha-meteoswiss/total.svg)](https://github.com/LNKtwo/ha-meteoswiss/releases)

**Swiss weather, alerts, pollen, and air quality for Home Assistant — powered by MeteoSwiss, Open-Meteo, and the Swiss federal open data platform.**

Current conditions from 293+ SwissMetNet stations, official MeteoSwiss weather alerts, measured pollen concentrations from 16 pollen stations, air quality data, 5-day forecasts, heating degree days (Heizgradtage), and more — all in one integration.

["MeteoSwiss Dashboard"](screenshot.png)

---

## ✨ Features

| Icon | Feature | Source | Details |
|:---:|---|---|---|
| 🌡️ | **Current Weather** | MeteoSwiss SwissMetNet | Temperature, humidity, wind, pressure, precipitation, dew point, sunshine, global radiation |
| 💨 | **Wind & Foehn** | MeteoSwiss | Wind speed, direction, gust peak (1-second), unique Foehn index |
| ❄️ | **Snow & Soil** | MeteoSwiss | Snow depth, soil temperatures at 5/10/20 cm depth |
| ⛅ | **Forecast** | Open-Meteo | Hourly + daily forecast (5 days), WMO weather code mapping |
| ⚠️ | **Weather Alerts** | MeteoSwiss App API | Official warnings: thunderstorm, rain, snow, wind, forest fire, flood |
| 🌸 | **Pollen (Forecast)** | Open-Meteo AQI | Birch, alder, grass, mugwort, ragweed forecast concentrations |
| 🔬 | **Pollen (Measured)** | MeteoSwiss ogd-pollen | Hourly measured pollen from 16 Swiss stations (birch, alder, hazel, beech, ash, grass) |
| 🌫️ | **Air Quality** | Open-Meteo AQI | PM2.5, PM10, NO₂, O₃ concentrations |
| 🏠 | **Heating Degree Days** | SIA 381/3 | Daily and seasonal Heizgradtage for energy monitoring |
| 🗺️ | **Stations Map** | MeteoSwiss | GeoJSON of all weather stations for map overlays |
| 🔁 | **Smart Caching** | Internal | TTL-based caching reduces API calls |
| 🛡️ | **Resilience** | Internal | Circuit breaker + exponential backoff retry |

---

## 📦 Installation

### Via HACS (recommended)

1. Go to **HACS** → **Integrations** → ⋮ → **Custom Repositories**
2. Add `https://github.com/LNKtwo/ha-meteoswiss` as category **Integration**
3. Search for **MeteoSwiss** → **Install**
4. Restart Home Assistant
5. **Settings** → **Devices & Services** → **Add Integration** → search **MeteoSwiss**

### Manual

1. Download the [`custom_components/meteoswiss/`](custom_components/meteoswiss/) folder
2. Copy it to your HA `custom_components/` directory
3. Restart Home Assistant
4. **Settings** → **Devices & Services** → **Add Integration** → search **MeteoSwiss**

---

## ⚙️ Configuration

The integration is set up entirely via Home Assistant's UI.

### Setup Options

| Field | Description | Required | Default |
|---|---|:---:|---|
| **Data Source** | `openmeteo` (global) or `meteoswiss` (Swiss stations) | ✅ | Open-Meteo |
| **Postal Code** | Swiss postal code for weather alerts (e.g. `8001`) | ✅ | — |
| **Station** | MeteoSwiss station (when using MeteoSwiss source) | ✅ | — |
| **Latitude / Longitude** | Coordinates (when using Open-Meteo source) | ✅ | Switzerland center |
| **Update Interval** | Refresh interval in seconds | ❌ | 600 (10 min) |

### Pollen Station Selection

In the integration options, you can select which MeteoSwiss pollen station provides measured pollen data:

| Code | Station |
|---|---|
| PBE | Bern |
| PBS | Basel |
| PBU | Buchs SG |
| PCF | La Chaux-de-Fonds |
| PDS | Davos / Wolfgang |
| PGE | Genève |
| PLO | Locarno / Monti |
| PLS | Lausanne |
| PLU | Lugano |
| PLZ | Luzern |
| PMU | Münsterlingen |
| PNE | Neuchâtel |
| PPY | Payerne |
| PSN | Sion |
| PZH | Zürich |
| BLR | Coldrerio / Mezzana |

---

## 📊 Sensor Reference

### Current Weather Sensors (MeteoSwiss SwissMetNet)

| Sensor | Unit | Device Class | Update |
|---|:---:|---|:---:|
| Temperature | °C | Temperature | 10 min |
| Humidity | % | Humidity | 10 min |
| Wind Speed | km/h | Wind Speed | 10 min |
| Wind Direction | ° | — | 10 min |
| Wind Gust (1s peak) | km/h | Wind Speed | 10 min |
| Pressure (QFF) | hPa | Pressure | 10 min |
| Precipitation | mm | Precipitation | 10 min |
| Dew Point | °C | Temperature | 10 min |
| Sunshine Duration | min | Duration | 10 min |
| Global Radiation | W/m² | Irradiance | 10 min |
| Snow Depth | cm | Distance | 10 min |
| Foehn Index | Code | — | 10 min |
| Soil Temperature 5 cm | °C | Temperature | 10 min |
| Soil Temperature 10 cm | °C | Temperature | 10 min |
| Soil Temperature 20 cm | °C | Temperature | 10 min |

### Air Quality Sensors (Open-Meteo)

| Sensor | Unit | Device Class | Update |
|---|:---:|---|:---:|
| PM2.5 | µg/m³ | PM2.5 | 30 min |
| PM10 | µg/m³ | PM10 | 30 min |
| Nitrogen Dioxide (NO₂) | µg/m³ | NO₂ | 30 min |
| Ozone (O₃) | µg/m³ | O₃ | 30 min |

### Pollen Sensors — Forecast (Open-Meteo)

| Sensor | Unit | Update |
|---|:---:|:---:|
| Birch Pollen | grains/m³ | 30 min |
| Alder Pollen | grains/m³ | 30 min |
| Grass Pollen | grains/m³ | 30 min |
| Mugwort Pollen | grains/m³ | 30 min |
| Ragweed Pollen | grains/m³ | 30 min |

### Pollen Sensors — Measured (MeteoSwiss)

| Sensor | Unit | Update |
|---|:---:|:---:|
| Birch Pollen (Measured) | No/m³ | 1 hour |
| Alder Pollen (Measured) | No/m³ | 1 hour |
| Hazel Pollen (Measured) | No/m³ | 1 hour |
| Beech Pollen (Measured) | No/m³ | 1 hour |
| Ash Pollen (Measured) | No/m³ | 1 hour |
| Grass Pollen (Measured) | No/m³ | 1 hour |

### Heating Degree Days (SIA 381/3)

| Sensor | Unit | Description |
|---|:---:|---|
| Heating Degree Days | °C·d | Daily HGt (12 °C threshold) |
| Season Heating Degree Days | °C·d | Accumulated since Oct 1 |

### Alert Binary Sensors (MeteoSwiss)

| Sensor | Description |
|---|---|
| Weather Alert | On when any active MeteoSwiss warning exists |
| Critical Weather Alert | On when level 3+ (significant danger) warning exists |

### Weather Entity

Provides current conditions + hourly (24h) and daily (5-day) forecasts via Open-Meteo.

---

## 🔌 Data Sources

| Source | API | Usage | Rate Limit |
|---|---|---|---|
| **MeteoSwiss SwissMetNet** | `data.geo.admin.ch` STAC | Current weather (10-min) | None (open data) |
| **MeteoSwiss Alerts** | `app-prod-ws.meteoswiss-app.ch` | Weather warnings | None |
| **MeteoSwiss Pollen** | `data.geo.admin.ch` ogd-pollen | Measured pollen (hourly) | None (open data) |
| **Open-Meteo Forecast** | `api.open-meteo.com` | Weather forecast (5 days) | 10k/day (free) |
| **Open-Meteo Air Quality** | `air-quality-api.open-meteo.com` | Pollen forecast, AQ | 10k/day (free) |

### Attribution

- Weather data: © [MeteoSwiss](https://www.meteoswiss.admin.ch/)
- Forecast data: [Open-Meteo](https://open-meteo.com/) (MIT License)
- Station metadata: [geo.admin.ch](https://data.geo.admin.ch/)

---

## 🌍 Languages

The integration includes full translations for all four Swiss national languages:

| Language | File |
|---|---|
| English | `translations/en.json` |
| Deutsch | `translations/de.json` |
| Français | `translations/fr.json` |
| Italiano | `translations/it.json` |

---

## ❓ FAQ

<details>
<summary><b>Which data source should I choose?</b></summary>

- **Open-Meteo**: Works anywhere on Earth. Best for general weather + forecast. No station needed.
- **MeteoSwiss**: Uses official Swiss weather stations (SwissMetNet). Best if you want real measured data from a station near you. Only works for Switzerland.

Both sources provide the forecast via Open-Meteo. The choice only affects current weather sensors.
</details>

<details>
<summary><b>Why do I see two sets of pollen sensors?</b></summary>

- **Forecast pollen** (Birch/Alder/Grass/Mugwort/Ragweed) comes from Open-Meteo's model — available everywhere.
- **Measured pollen** (Birch/Alder/Hazel/Beech/Ash/Grass) comes from MeteoSwiss stations — actual measured concentrations, more accurate but only for Switzerland.
</details>

<details>
<summary><b>The weather condition shows "partly cloudy" at night — is this normal?</b></summary>

The integration resolves the current condition with a fallback chain: Open-Meteo current weather code → MeteoSwiss symbol → precipitation-based fallback → day/night fallback. If no precise data is available, a safe default is used.
</details>

<details>
<summary><b>How do Heizgradtage (Heating Degree Days) work?</b></summary>

Uses Swiss standard SIA 381/3: heating threshold is 12 °C daily mean. HGt = max(0, 12 − daily_mean). Heating season runs from October 1 to April 30.
</details>

<details>
<summary><b>I'm outside Switzerland — can I use this?</b></summary>

Yes! Select **Open-Meteo** as your data source and enter your coordinates. You'll get current weather, forecasts, air quality, and forecast pollen. MeteoSwiss alerts and measured pollen are Switzerland-only.
</details>

---

## 🆚 Comparison

| Feature | Met.no | OpenWeatherMap | Pirate Weather | **MeteoSwiss** |
|---|:---:|:---:|:---:|:---:|
| Swiss station data | ❌ | ❌ | ❌ | ✅ 293+ stations |
| Official CH alerts | ❌ | ❌ | ❌ | ✅ |
| Measured pollen | ❌ | ❌ | ❌ | ✅ 16 stations |
| Foehn index | ❌ | ❌ | ❌ | ✅ |
| Snow depth | ❌ | ❌ | ❌ | ✅ |
| Heating degree days | ❌ | ❌ | ❌ | ✅ SIA 381/3 |
| Free / no API key | ✅ | ❌ | ✅ | ✅ |
| Forecast | ✅ | ✅ | ✅ | ✅ |

---

## 📋 Requirements

- Home Assistant **2024.7** or newer
- Internet connection (cloud polling integration)

---

## 📖 Documentation

- [Full Sensor Reference](docs/SENSORS.md)
- [API Sources & Attribution](docs/API_SOURCES.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

---

## 🤝 Support

- **Bug reports:** [GitHub Issues](https://github.com/LNKtwo/ha-meteoswiss/issues)
- **Discussions:** [GitHub Discussions](https://github.com/LNKtwo/ha-meteoswiss/discussions)
- **HACS:** Search "MeteoSwiss" in HACS

---

## 📜 License

[MIT](LICENSE)

---

*Data: [MeteoSwiss](https://www.meteoswiss.admin.ch/) · Forecast: [Open-Meteo](https://open-meteo.com/) · Made with ❤️ for the Swiss HA community*
