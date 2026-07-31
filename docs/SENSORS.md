# Sensor Reference

Complete documentation of all entities provided by the MeteoSwiss integration.

---

## Weather Entity

| Property | Value |
|---|---|
| Platform | `weather` |
| Forecast | Hourly (24h) + Daily (5 days) |
| Source | Open-Meteo |
| Update Interval | 1 hour |
| Units | °C, hPa, km/h, mm |

Provides current conditions (temperature, humidity, pressure, wind, precipitation) and forecasts via Open-Meteo's API. Conditions are mapped from WMO weather codes to Home Assistant condition strings.

---

## Sensor Entities

### Current Weather (MeteoSwiss SwissMetNet)

Data from `data.geo.admin.ch` STAC API, 10-minute granularity.

| Sensor Key | Name | Unit | Device Class | State Class | Parameter |
|---|---|:---:|---|---|---|
| `temperature` | Temperature | °C | Temperature | Measurement | `tre200s0` |
| `humidity` | Humidity | % | Humidity | Measurement | `ure200s0` |
| `wind_speed` | Wind Speed | km/h | Wind Speed | Measurement | `fu3010z0` |
| `wind_direction` | Wind Direction | ° | — | Measurement | `dkl010z0` |
| `wind_gust` | Wind Gust | km/h | Wind Speed | Measurement | `fu3010z1` |
| `pressure` | Pressure | hPa | Pressure | Measurement | `pp0qffs0` |
| `precipitation` | Precipitation | mm | Precipitation | Measurement | `rre150z0` |
| `dew_point` | Dew Point | °C | Temperature | Measurement | `tde200s0` (measured, with Magnus fallback) |
| `sunshine_duration` | Sunshine Duration | min | Duration | Measurement | `sre000z0` |
| `global_radiation` | Global Radiation | W/m² | Irradiance | Measurement | `gre000z0` |
| `snow_depth` | Snow Depth | cm | Distance | Measurement | `htoauts0` |
| `foehn_index` | Foehn Index | Code | — | Measurement | `wcc006s0` |
| `soil_temperature_5cm` | Soil Temperature 5 cm | °C | Temperature | Measurement | `tso005s0` |
| `soil_temperature_10cm` | Soil Temperature 10 cm | °C | Temperature | Measurement | `tso010s0` |
| `soil_temperature_20cm` | Soil Temperature 20 cm | °C | Temperature | Measurement | `tso020s0` |

### Air Quality (Open-Meteo Air Quality API)

| Sensor Key | Name | Unit | Device Class | Update |
|---|---|:---:|---|:---:|
| `pm25` | PM2.5 | µg/m³ | PM2.5 | 30 min |
| `pm10` | PM10 | µg/m³ | PM10 | 30 min |
| `nitrogen_dioxide` | Nitrogen Dioxide | µg/m³ | NO₂ | 30 min |
| `ozone` | Ozone | µg/m³ | O₃ | 30 min |

### Pollen — Forecast (Open-Meteo Air Quality API)

Modelled pollen concentrations (grains/m³).

| Sensor Key | Name | Thresholds (Low/Mod/High) |
|---|---|---|
| `pollen_birch` | Birch Pollen | 10 / 50 / 200 |
| `pollen_alder` | Alder Pollen | 10 / 50 / 200 |
| `pollen_grass` | Grass Pollen | 5 / 20 / 50 |
| `pollen_mugwort` | Mugwort Pollen | 10 / 50 / 200 |
| `pollen_ambrosia` | Ragweed Pollen | 5 / 20 / 50 |

### Pollen — Measured (MeteoSwiss ogd-pollen)

Hourly measured pollen concentrations (No/m³) from Swiss pollen stations.

| Sensor Key | Name | Parameter |
|---|---|---|
| `ms_pollen_birch` | Birch Pollen (Measured) | `kabetuh0` |
| `ms_pollen_alder` | Alder Pollen (Measured) | `kaalnuh0` |
| `ms_pollen_hazel` | Hazel Pollen (Measured) | `kacoryh0` |
| `ms_pollen_beech` | Beech Pollen (Measured) | `kafaguh0` |
| `ms_pollen_ash` | Ash Pollen (Measured) | `kafraxh0` |
| `ms_pollen_grass` | Grass Pollen (Measured) | `khpoach0` |

Attributes include: current value, 24h history, station ID, source attribution.

### Heating Degree Days (SIA 381/3)

| Sensor Key | Name | Unit | State Class | Description |
|---|---|:---:|---|---|
| `heating_degree_days` | Heating Degree Days | °C·d | Measurement | Daily HGt = max(0, 12 − daily_mean_temp) |
| `season_heating_degree_days` | Season Heating Degree Days | °C·d | Total Increasing | Accumulated HGt since Oct 1 |

**Standard:** SIA 381/3 — Swiss heating degree days.
**Threshold:** 12 °C daily mean temperature.
**Season:** October 1 – April 30.

### Diagnostic Sensors

| Sensor Key | Name | Entity Category | Description |
|---|---|---|---|
| `stations_map` | Weather Stations | Diagnostic | Count + GeoJSON of all SwissMetNet stations |
| `cache_stats` | Cache Statistics | Diagnostic | Hit rate, entries, evictions per cache |

---

## Binary Sensor Entities

### Weather Alerts (MeteoSwiss App API)

| Sensor Key | Name | Device Class | Trigger |
|---|---|---|---|
| `any_alert` | Weather Alert | Safety | Any active MeteoSwiss warning |
| `critical_alert` | Critical Weather Alert | Safety | Active warning at level 3+ (significant danger) |

**Attributes:** `active_alerts_count`, `alerts` (list of alert dicts with type, level, description, valid period).

**Warning types:** Thunderstorm (1), Rain (2), Snow (3), Wind (4), Forest Fire (10), Flood (11).

**Warning levels:** 1 = No/minor danger, 2 = Moderate, 3 = Significant, 4 = High, 5 = Very high.
