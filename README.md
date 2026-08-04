# 🇨🇭 MeteoSwiss for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/LNKtwo/ha-meteoswiss)
[![Version](https://img.shields.io/badge/version-8.1.0-blue.svg)](https://github.com/LNKtwo/ha-meteoswiss/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![HA Min Version](https://img.shields.io/badge/HA-2024.7%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Downloads](https://img.shields.io/github/downloads/LNKtwo/ha-meteoswiss/total.svg)](https://github.com/LNKtwo/ha-meteoswiss/releases)

**Swiss weather, alerts, pollen, and air quality for Home Assistant — powered by MeteoSwiss, Open-Meteo, and the Swiss federal open data platform.**

Current conditions from 293+ SwissMetNet stations, official MeteoSwiss weather alerts, measured pollen concentrations from 16 pollen stations, air quality data, 5-day forecasts, heating degree days (Heizgradtage), UV index, and more — all in one integration.

Companion card: **[ha-meteoswiss-card](https://github.com/LNKtwo/ha-meteoswiss-card)** — iOS Weather inspired glassmorphism dashboard card.

---

## ✨ Features

| Icon | Feature | Source | Details |
|:---:|---|---|---|
| 🌡️ | **Current Weather** | MeteoSwiss SwissMetNet | Temperature, humidity, wind, pressure, precipitation, dew point, sunshine, global radiation |
| 💨 | **Wind & Foehn** | MeteoSwiss | Wind speed, direction, gust peak (1-second), unique Foehn index |
| ❄️ | **Snow & Soil** | MeteoSwiss | Snow depth, soil temperatures at 5/10/20 cm depth |
| ☀️ | **UV Index** | Open-Meteo | Current UV index |
| ⛅ | **Forecast** | Open-Meteo | Hourly + daily forecast (5 days), WMO weather code mapping |
| ⚠️ | **Weather Alerts** | MeteoSwiss App API | Official warnings: thunderstorm, rain, snow, wind, forest fire, flood |
| 🌸 | **Pollen (Forecast)** | Open-Meteo AQI | Birch, alder, grass, mugwort, ragweed forecast concentrations |
| 🔬 | **Pollen (Measured)** | MeteoSwiss ogd-pollen | Hourly measured pollen from 16 Swiss stations (birch, alder, hazel, beech, ash, grass) |
| 🌫️ | **Air Quality** | Open-Meteo AQI | PM2.5, PM10, NO₂, O₃ concentrations |
| 🏠 | **Heating Degree Days** | SIA 381/3 | Daily and seasonal Heizgradtage for energy monitoring |
| 🗺️ | **Stations Map** | MeteoSwiss | GeoJSON of all weather stations for map overlays |

---

## 📦 Installation

### Via HACS (recommended)

1. Open **HACS** → **Integrations**
2. Click **⋮** → **Custom repositories**
3. Add:
   - **URL:** `https://github.com/LNKtwo/ha-meteoswiss`
   - **Category:** Integration
4. Search for **"MeteoSwiss"** → **Install**
5. Restart Home Assistant
6. **Settings → Devices & Services → Add Integration** → search **"MeteoSwiss"**
7. Choose your station (e.g. `LUZ` for Luzern) or enter postal code

### Manual

1. Download `custom_components/meteoswiss/` from the [latest release](../../releases)
2. Copy to your `config/custom_components/meteoswiss/` directory
3. Restart Home Assistant
4. **Settings → Devices & Services → Add Integration** → **MeteoSwiss**

---

## ⚙️ Configuration

The integration is configured via the UI (config flow). After installation:

1. **Settings → Devices & Services → Add Integration → MeteoSwiss**
2. Select your weather station by code (e.g. `LUZ`, `BER`, `BAS`) or enter your postal code
3. The integration auto-detects your coordinates for forecast and pollen data

### Options

| Option | Default | Description |
|--------|---------|-------------|
| Station | required | SwissMetNet station code (e.g. `LUZ`) |
| Update interval | 600s | Data refresh interval (minimum 600s) |
| Pollen station | `PLZ` | MeteoSwiss pollen measurement station |
| Data source | MeteoSwiss | `meteoswiss` (SwissMetNet) or `openmeteo` (Open-Meteo) |

---

## 🌍 Available Stations

293+ SwissMetNet stations across Switzerland. Find your station on the [MeteoSwiss measurement network map](https://www.meteoswiss.admin.ch/services-and-publications/applications/measurement-values-and-measuring-networks.html).

Common stations:

| Code | Location |
|------|----------|
| LUZ | Luzern |
| BER | Bern |
| BAS | Basel |
| GUT | Güttingen (Bodensee) |
| SMA | Zürich (SMA) |
| CHA | Chur |
| SIO | Sion |
| GVE | Genève |

---

## 📊 Sensors

All sensors are auto-created. Availability depends on what each station physically measures.

| Sensor | Unit | Source |
|--------|------|--------|
| Temperature | °C | SwissMetNet |
| Humidity | % | SwissMetNet |
| Wind Speed | km/h | SwissMetNet |
| Wind Direction | ° | SwissMetNet |
| Wind Gust | km/h | SwissMetNet |
| Pressure | hPa | SwissMetNet |
| Dew Point | °C | SwissMetNet |
| Sunshine Duration | min | SwissMetNet |
| Global Radiation | W/m² | SwissMetNet |
| Snow Depth | cm | SwissMetNet |
| Foehn Index | Code | SwissMetNet |
| Soil Temperature 5/10/20 cm | °C | SwissMetNet |
| UV Index | Index | Open-Meteo |
| PM2.5 / PM10 | μg/m³ | Open-Meteo AQI |
| NO₂ / O₃ | μg/m³ | Open-Meteo AQI |
| Pollen (Forecast) | grains/m³ | Open-Meteo AQI |
| Pollen (Measured) | particles/m³ | MeteoSwiss |
| Heating Degree Days | °C·d | SIA 381/3 |

---

## 🔗 Companion Card

**[ha-meteoswiss-card](https://github.com/LNKtwo/ha-meteoswiss-card)** — iOS Weather inspired glassmorphism dashboard card with:
- Animated weather backgrounds (rain, snow, hail, lightning, clouds)
- Hourly charts (temperature, precipitation, sunshine, wind)
- 7-day forecast diagram
- Weather warnings with color-coded badges
- Pollen levels
- Swiss-specific values (Foehn, snow depth, freezing level, heating degree days)

---

## 🛠️ Development

```bash
git clone https://github.com/LNKtwo/ha-meteoswiss.git
cd ha-meteoswiss
```

Files are in `custom_components/meteoswiss/`. Test by symlinking into your HA config.

---

## 📝 License

MIT — see [LICENSE](LICENSE)
