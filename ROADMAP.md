# 🗺️ Roadmap

## Done

### v6.0.0 — Stable Foundation (2026-07-31)
- ✅ Shared aiohttp session (fixed session leak)
- ✅ Circuit breaker pattern
- ✅ Smart TTL caching
- ✅ Exponential backoff retry
- ✅ Proper device info & entity categories
- ✅ Centralized WMO weather code mapping
- ✅ Forecast coordinator (Open-Meteo)
- ✅ Weather alerts (MeteoSwiss App API)
- ✅ Pollen forecast (Open-Meteo Air Quality)

### v6.1.0 — Resilience (2026-07-31)
- ✅ 30-second API timeout on all requests
- ✅ Circuit breaker (5 failures → 5 min pause)

### v7.0.0 — Major Features (2026-07-31)
- ✅ Snow depth sensor (`htoauts0`)
- ✅ Foehn index sensor (`wcc006s0`)
- ✅ Soil temperature sensors (5/10/20 cm)
- ✅ Measured dew point (`tde200s0`) with Magnus fallback
- ✅ Air quality sensors (PM2.5, PM10, NO₂, O₃)
- ✅ MeteoSwiss measured pollen (16 stations, 6 types)
- ✅ Heating degree days (SIA 381/3)
- ✅ Forecast extensions (snowfall, freezing level)
- ✅ SLF/BAFU/Camera API research documented (placeholders)

### v7.0.1 — Hotfix (2026-07-31)
- ✅ Removed diagnostics.py (used non-existent HA API)

### v8.0.0 — Production Release (2026-07-31)
- ✅ Professional README with full documentation
- ✅ Complete translations (de/en/fr/it) — all entities covered
- ✅ docs/SENSORS.md — sensor reference
- ✅ docs/API_SOURCES.md — API documentation
- ✅ Code cleanup — zero unused imports, zero undefined types
- ✅ quality_scale: platinum in manifest
- ✅ iot_class in hacs.json

---

## Future Ideas

### Under Consideration

| Idea | Source | Value | Effort |
|---|---|---|---|
| **MeteoSwiss localised forecast** | `ch.meteoschweiz.ogd-local-forecasting` | Replace Open-Meteo with MeteoSwiss app forecast (ICON-CH blend) | M |
| **Precipitation radar camera** | MeteoSwiss CombiPrecip | Visual radar map entity | M |
| **SLF avalanche bulletin** | SLF / whiterisk.ch | Danger levels per Alpine region | M |
| **BAFU flood warnings** | hydrodaten.admin.ch | River level warnings | M |
| **Swiss natural hazards portal** | natural-hazards.ch | Unified hazard feed (floods, quakes, fires) | L |
| **Custom Lovelace card** | — | Unified Swiss weather dashboard card | L |
| **Granular sensor toggles** | — | Enable/disable individual sensors in options | M |
| **MeteoSwiss ICON-CH1 model** | CSCS object storage | 1km resolution forecast model | XL |
| **Historical weather data** | Open-Meteo Archive | Climate tracking, anomaly detection | L |
| **Evapotranspiration** | MeteoSwiss / Open-Meteo | FAO ET₀ for irrigation control | S |
| **UV index forecast** | Open-Meteo | Hourly UV forecast (skin cancer prevention) | S |
| **Nowcast (precipitation 30-min)** | Open-Meteo | Precipitation nowcast | S |

### Not Planned

| Idea | Reason |
|---|---|
| ML-powered weather insights | Too complex, minimal user value |
| Real-time radar animation | Requires GRIB2 processing, too heavy |

---

*This roadmap reflects the current state of available public APIs. New features depend on data providers publishing documented APIs.*
