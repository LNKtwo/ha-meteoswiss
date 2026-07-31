# ha-meteoswiss Product Roadmap

**Version:** 1.0 — 2026-07-31  
**Author:** Senior Product Engineer Analysis  
**Current version:** v6.1.2 (3,775 LOC, 16 Python files)

---

## Executive Summary

ha-meteoswiss is a solid v6 integration with 4 data pipelines (MeteoSwiss STAC, Open-Meteo Forecast, Open-Meteo Air Quality/Pollen, MeteoSwiss App Alerts). The architecture is clean — shared sessions, circuit breakers, smart caching, retry with backoff. However, the integration only scratches the surface of what MeteoSwiss and Open-Meteo offer. There are **23 MeteoSwiss STAC collections** (we use 1), **130+ measurement parameters** (we use 10), and **6+ Swiss-specific data sources** (SLF, BAFU, MeteoSwiss Pollen Network) completely untapped.

---

## Analysis

### 1. MeteoSwiss — What's Not Used

#### 1a. STAC Collections (23 total, 1 used)

| Collection | Status | Value |
|---|---|---|
| `ch.meteoschweiz.ogd-smn` | ✅ Used (10-min current weather) | Core |
| `ch.meteoschweiz.ogd-pollen` | ❌ **Unused** | **HIGH** — 16 stations, hourly/daily pollen *measurements* (not model data) |
| `ch.meteoschweiz.ogd-phenology` | ❌ Unused | LOW — 175 stations, yearly phenophase observations (niche) |
| `ch.meteoschweiz.ogd-obs` | ❌ Unused | LOW — 7 stations, visual human observations (visibility, clouds) |
| `ch.meteoschweiz.ogd-nbcn` | ❌ Unused | MED — Homogeneous climate data series (long-term, quality-controlled) |
| `ch.meteoschweiz.ogd-forecasting-icon-ch1` | ❌ **Unused** | **HIGH** — 1km ICON-CH1-EPS forecast model (Swiss-specific, 33h, every 3h) |
| `ch.meteoschweiz.ogd-forecasting-icon-ch2` | ❌ **Unused** | **MED** — 2km ICON-CH2-EPS forecast model |
| `ch.meteoschweiz.ogd-local-forecasting` | ❌ **Unused** | **CRITICAL** — Same data as MeteoSwiss app! Hourly forecast per PLZ, +0h to +192h |
| `ch.meteoschweiz.ogd-radar-precip` | ❌ **Unused** | **HIGH** — 5-min radar precipitation (PRECIP, CombiPrecip) |
| `ch.meteoschweiz.ogd-radar-hail` | ❌ Unused | MED — POH/MESHS hail probability |
| `ch.meteoschweiz.ogd-smn-precip` | ❌ Unused | MED — Separate precipitation stations (10-min) |
| `ch.meteoschweiz.ogd-smn-tower` | ❌ Unused | LOW — Tower measurements (tall masts) |
| `ch.meteoschweiz.ogd-surface-derived-grid` | ❌ Unused | MED — Spatial grids (RhiresD, TabsD, etc.) |
| `ch.meteoschweiz.ogd-satellite-derived-grid` | ❌ Unused | LOW — Radiation/cloud satellite grids |
| `ch.meteoschweiz.ogd-climate-normals-grid` | ❌ Unused | LOW — Climate normals (30-year averages) |

#### 1b. SwissMetNet Parameters (130+ available, 10 used)

**Currently used (10-min granularity):**
- `tre200s0` — Temperature 2m
- `ure200s0` — Humidity 2m
- `fu3010z0` — Wind speed 10-min mean (km/h)
- `dkl010z0` — Wind direction
- `pp0qffs0` — Pressure QFF
- `rre150z0` — Precipitation 10-min sum
- `fu3010z1` — Gust peak 1-second
- `sre000z0` — Sunshine duration
- `gre000z0` — Global radiation
- Dew point (calculated, not measured)

**High-value parameters NOT used:**

| Parameter | Description | Granularity | Value |
|---|---|---|---|
| `htoauts0` | **Snow depth** (automatic, current) | T (10min) | **HIGH** — Critical for Swiss winter |
| `fu3010z3` | Gust peak 3-second | T | MED — More standard than 1-sec gust |
| `tde200s0` | **Dew point** (measured, not calculated) | T | MED — More accurate than Magnus formula |
| `tresurs0` | **Surface temperature** | T | MED — Frost warning, road conditions |
| `tso005s0` | **Soil temperature** 5cm | T | MED — Gardening, agriculture |
| `tso010s0` | Soil temperature 10cm | T | LOW |
| `tso020s0` | Soil temperature 20cm | T | LOW |
| `xchills0` | **Chill temperature** (wind chill) | T | MED — Already calculated by HA? |
| `wcc006s0` | **Foehn index** | T | **HIGH** — Unique Swiss weather phenomenon |
| `pva200s0` | Vapour pressure | T | LOW |
| `pp0qnhs0` | Pressure QNH (standard atmosphere) | T | LOW |
| `ppz850s0` | Geopotential 850 hPa | T | LOW — Aviation |
| `ods000z0` | **Diffuse radiation** | T | MED — Solar panel owners |
| `oli000z0` | Longwave incoming radiation | T | LOW |
| `olo000z0` | Longwave outgoing radiation | T | LOW |
| `osr000z0` | Shortwave reflected radiation | T | LOW |
| `fve010z0` | Wind speed vectorial | T | LOW |
| `erefaoh0` | **FAO reference evapotranspiration** | H/D/M/Y | **MED** — Gardening/irrigation |

**Daily/Monthly/Yearly parameters not used (aggregate values):**
- `tre200dn/dx` — Daily min/max temperature
- `rre150d0` — Daily precipitation total (6-6 UTC)
- `rka150d0` — Daily precipitation total (0-0 UTC)
- `sre000d0` — Daily sunshine total (minutes)
- `tnd00nm0` — Frost days count (monthly)
- `tnd25xm0` — Summer days count (monthly)
- `tnd30xm0` — Heat days count (monthly)
- `xcd000d0` — Cooling Degree Days
- `xno000d0` — Heating Degree Days

#### 1c. MeteoSwiss Pollen Network (`ch.meteoschweiz.ogd-pollen`)

**16 stations** with **measured** (not modelled) pollen concentrations:

| Pollen Type | Parameter | Granularity |
|---|---|---|
| Alder (Erle) | `kaalnuh0` | Hourly |
| Birch (Birke) | `kabetuh0` | Hourly |
| Hazel (Hasel) | `kacoryh0` | Hourly |
| Beech (Buche) | `kafaguh0` | Hourly |
| Ash (Esche) | `kafraxh0` | Hourly |
| Oak (Eiche) | `kaquerh0` | Hourly |
| Grasses (Gräser) | `khpoach0` | Hourly |
| Mugwort (Beifuss) | `kabearh0` | Hourly |
| Ragweed (Ambrosia) | `kaambh0` | Hourly |
| Plantain (Wegerich) | `kaplah0` | Hourly |
| Nettle (Nessel) | `kaurtih0` | Hourly |
| Sorrel (Ampfer) | `karumh0` | Hourly |
| **Plus**: Daily averages and annual integrals | | D, Y |

This is **far more comprehensive** than the Open-Meteo pollen data (5 types). MeteoSwiss measures 13+ pollen types vs. Open-Meteo's 5.

#### 1d. MeteoSwiss Localised Forecasting (`ch.meteoschweiz.ogd-local-forecasting`)

This is the **same forecast used in the MeteoSwiss app** — a multi-model blend (INCA, ICON-CH1-EPS, ICON-CH2-EPS, ECMWF). Currently, the integration uses Open-Meteo for forecasts, which does NOT have the Swiss-specific ICON model blend. This would replace the Open-Meteo forecast with the authoritative Swiss forecast.

### 2. Open-Meteo — What's Not Used

**Currently used:** Forecast API (temperature, humidity, precip, wind, weather_code) + Air Quality API (pollen only)

**Available but unused:**

| API | Variables | Value for CH |
|---|---|---|
| **Air Quality: PM10, PM2.5, NO2, SO2, O3, CO** | European AQI, US AQI | **HIGH** — Swiss air quality (CAMS 11km) |
| **Air Quality: UV Index** | Current + hourly | **HIGH** — Currently from Open-Meteo current only |
| **Forecast: soil_temperature, soil_moisture** | 0-81cm depths | MED — Gardening |
| **Forecast: snowfall, snow_depth** | cm, meters | **HIGH** — Swiss winter |
| **Forecast: freezing_level_height** | meters | **HIGH** — Snow/rain line (critical for CH) |
| **Forecast: cape** | J/kg | MED — Thunderstorm prediction |
| **Forecast: visibility** | meters | MED — Fog, driving conditions |
| **Forecast: cloud_cover (low/mid/high)** | % | MED — Better condition mapping |
| **Forecast: et0_fao_evapotranspiration** | mm | MED — Irrigation |
| **Forecast: vapour_pressure_deficit** | kPa | LOW — Plant stress |
| **Marine API** | Wave height, etc. | LOW — Only Geneva/Lakes |
| **Flood API** | River discharge (GloFAS) | MED — Aare, Rhine, Ticino |
| **Climate API** | Historical scenarios | LOW — Research use |
| **Geocoding API** | Place names → coords | MED — Better UX in config flow |
| **Historical Weather (Archive)** | Past weather data | MED — Climate tracking |

### 3. HA Integration Features — Competitive Analysis

| Feature | Met.no | OWM | Pirate Weather | **ha-meteoswiss** |
|---|---|---|---|---|
| `forecast_hours` / `forecast_days` | ✅ | ✅ | ✅ | ✅ |
| `forecast_nowcasts` (30-min) | ✅ | ❌ | ❌ | ❌ |
| **Camera entity (radar/satellite)** | ❌ | ❌ | ❌ | ❌ |
| **Image entity (weather map)** | ❌ | ❌ | ❌ | ❌ |
| **Websocket services** | ✅ | ❌ | ❌ | ❌ |
| **Diagnostics config flow** | ✅ | ✅ | ✅ | ❌ |
| **Repair issues** | ✅ | ❌ | ❌ | ❌ |
| **Entity re-polling service** | ✅ | ❌ | ❌ | ❌ |
| **Multiple forecast days configurable** | ✅ | ✅ | ❌ | ❌ (hardcoded 5) |
| **Translations (fr/it)** | ✅ | ✅ | ✅ | ❌ (de/en only) |

### 4. Swiss-Specific Features

| Feature | Source | Status | Value |
|---|---|---|---|
| **Lawinenbulletin (Avalanche)** | SLF/WSL | ❌ Not integrated | **HIGH** — Switzerland has the most avalanche deaths per capita |
| **Hochwasserwarnungen (Flood)** | BAFU / FOEN | Partially (MeteoSwiss app has level 11) | **HIGH** — Rhine, Aare, Ticino, Rhône |
| **UV-Index** | MeteoSwiss / O-M | Partially (O-M current only) | **MED** — Skin cancer prevention |
| **Ozon (O3)** | MeteoSwiss / O-M AQ | ❌ Not integrated | **MED** — Summer smog in Ticino/Mittelland |
| **Pollen from MeteoSwiss** | MeteoSwiss (16 stations) | ❌ Using O-M model instead | **HIGH** — Measured >> modelled |
| **Foehn index** | MeteoSwiss | ❌ Not used | **HIGH** — Unique Swiss concern (Alps) |
| **Snow depth** | MeteoSwiss | ❌ Not used | **HIGH** — Winter tourism, avalanche risk |
| **Heizgradtage (HGT)** | MeteoSwiss | ❌ Not used | **MED** — Energy monitoring, heating optimization |
| **Natural Hazards Portal** | natural-hazards.ch | ❌ Not integrated | **MED** — Unified Swiss hazard warnings |

### 5. UX/Design

| Area | Status | Gap |
|---|---|---|
| **Lovelace Card** | ❌ None | No custom card — users only get default HA weather card |
| **Translations** | de, en | Missing fr, it (Swiss national languages!) |
| **Diagnostics** | ❌ None | No `diagnostics.py` config flow for troubleshooting |
| **Repair issues** | ❌ None | No `repairs.py` for proactive issue detection |
| **Config flow validation** | Basic | No coordinate validation, no station lookup by name |
| **Options flow** | Minimal | Only update_interval — no granular sensor toggles |
| **Device grouping** | OK | Could separate alerts/pollen into sub-devices |

### 6. Community / Distribution

| Area | Status | Opportunity |
|---|---|---|
| **HACS** | ✅ Listed | Not "Featured" — needs more stars/installs |
| **ClawHub** | ❌ Not published | Publish as OpenClaw skill for broader reach |
| **GitHub stars** | Unknown | Community contributions welcome |
| **Documentation** | README exists | Needs setup guide, screenshots, troubleshooting |

---

## Roadmap

### TIER 1: Quick Wins (1-2 days each, high user value)

---

#### T1.1: Snow Depth Sensor
**Description:** Add `htoauts0` (snow depth, automatic measurement, current value) from SwissMetNet 10-min data. Already fetched by the coordinator — just needs a new sensor entity.  
**Aufwand:** S (2-3 hours)  
**Nutzerwert:** High — Critical for Swiss winter, ski areas, avalanche awareness  
**Machbarkeit:** Very High — Data already in CSV, just not parsed  
**Implementation:** Add `SENSOR_SNOW_DEPTH` to const.py, parse `htoauts0` in coordinator, add SensorEntityDescription  

---

#### T1.2: Measured Dew Point
**Description:** Replace the Magnus formula calculation with MeteoSwiss measured dew point `tde200s0`.  
**Aufwand:** S (1 hour)  
**Nutzerwert:** Med — More accurate, especially at extremes  
**Machbarkeit:** Very High — Same CSV, same coordinator  
**Implementation:** Parse `tde200s0`, use measured value with calculated fallback  

---

#### T1.3: Foehn Index Sensor
**Description:** Add `wcc006s0` (Foehn index) — a uniquely Swiss parameter that indicates foehn wind conditions.  
**Aufwand:** S (1-2 hours)  
**Nutzerwert:** High in Alpine regions — foehn causes rapid temp changes, fires, avalanches  
**Machbarkeit:** Very High — Data in same CSV  
**Implementation:** New sensor, translate foehn index codes  

---

#### T1.4: Soil Temperature Sensors
**Description:** Add `tso005s0`, `tso010s0`, `tso020s0` (soil temperature at 5/10/20cm depth).  
**Aufwand:** S (1-2 hours)  
**Nutzerwert:** Med — Gardening, agriculture, permafrost monitoring  
**Machbarkeit:** Very High — Same CSV  
**Implementation:** 3 new sensor entities  

---

#### T1.5: French & Italian Translations
**Description:** Add `fr.json` and `it.json` translations — Switzerland has 4 national languages. Currently only de/en.  
**Aufwand:** S (2-3 hours)  
**Nutzerwert:** High — Swiss fr/it speakers can't use integration in their language  
**Machbarkeit:** Very High — Copy en.json, translate strings  
**Implementation:** Create translations/fr.json, translations/it.json  

---

#### T1.6: Diagnostics Config Flow
**Description:** Add a diagnostics step to config flow for troubleshooting (dump coordinator data, API URLs, station info).  
**Aufwand:** S (2-3 hours)  
**Nutzerwert:** Med — Easier support, faster bug resolution  
**Machbarkeit:** Very High — Standard HA pattern  
**Implementation:** Add `diagnostics.py` with data dump  

---

#### T1.7: Air Quality Sensors (PM2.5, NO2, O3, AQI)
**Description:** Extend the Open-Meteo Air Quality coordinator to fetch PM10, PM2.5, NO2, SO2, O3, CO, European AQI, UV Index. Currently only pollen is fetched from this API.  
**Aufwand:** S-M (4-6 hours)  
**Nutzerwert:** High — Air quality is a top concern in Swiss summer (ozone in Ticino/Mittelland)  
**Machbarkeit:** Very High — Same API, same coordinator, just add variables  
**Implementation:** Extend `pollen_coordinator_openmeteo.py` → rename to `airquality_coordinator.py`, add new sensors  

---

#### T1.8: Forecast Extensions (Snowfall, Freezing Level, Visibility, Cloud Cover)
**Description:** Add `snowfall`, `freezing_level_height`, `visibility`, `cloud_cover` to Open-Meteo forecast request.  
**Aufwand:** S (2-3 hours)  
**Nutzerwert:** High — Freezing level is critical for snow/rain boundary in mountains  
**Machbarkeit:** Very High — Just add params to existing API call  
**Implementation:** Extend URL params in `forecast_coordinator.py`  

---

### TIER 2: Major Features (1-2 weeks each)

---

#### T2.1: MeteoSwiss Measured Pollen (Replace Open-Meteo Pollen)
**Description:** Replace Open-Meteo modelled pollen with MeteoSwiss **measured** pollen from 16 stations (`ch.meteoschweiz.ogd-pollen`). MeteoSwiss measures 13+ pollen types hourly vs. Open-Meteo's 5 modelled types.  
**Aufwand:** M (3-5 days)  
**Nutzerwert:** High — Measured >> modelled, more pollen types, Swiss data  
**Machbarkeit:** High — Same STAC API pattern as SwissMetNet, new coordinator  
**Implementation:**  
- New `pollen_coordinator_meteoswiss.py` following the same STAC pattern as `coordinator.py`  
- Config flow: add pollen station selection (nearest station to PLZ)  
- Map 13 pollen types: alder, birch, hazel, beech, ash, oak, grass, mugwort, ragweed, plantain, nettle, sorrel + more  
- Keep Open-Meteo pollen as fallback for stations outside CH or off-season  

---

#### T2.2: MeteoSwiss Localised Forecasting
**Description:** Replace Open-Meteo forecast with MeteoSwiss localised forecasting data (`ch.meteoschweiz.ogd-local-forecasting`) — the **same multi-model blend used in the MeteoSwiss app** (INCA + ICON-CH1-EPS + ICON-CH2-EPS + ECMWF). Available per PLZ, per station, per POI.  
**Aufwand:** M (5-7 days)  
**Nutzerwert:** High — Swiss-specific model blend beats generic Open-Meteo in CH  
**Machbarkeit:** Med — Need to research the data format (likely GRIB2 or NetCDF for grid, but point data should be simpler)  
**Implementation:**  
- Research `ch.meteoschweiz.ogd-local-forecasting` data format and access pattern  
- New `localforecast_coordinator.py`  
- Config flow option: forecast source (Open-Meteo vs MeteoSwiss)  
- Map MeteoSwiss forecast symbols to HA conditions  

---

#### T2.3: Precipitation Radar Camera/Image Entity
**Description:** Add a HA camera or image entity showing the MeteoSwiss precipitation radar (CombiPrecip / PRECIP product from `ch.meteoschweiz.ogd-radar-precip`). Updates every 5 minutes.  
**Aufwand:** M (3-5 days)  
**Nutzerwert:** High — Visual weather radar is the #1 requested feature in weather integrations  
**Machbarkeit:** Med — Radar data is GRIB2 grids; need WMS/TMS service or render from raw data. Check `wms.geo.admin.ch` for tiled images.  
**Implementation:**  
- Research `https://wms.geo.admin.ch/` for radar WMS layers  
- Create camera entity that polls for latest radar tile/image  
- Configurable: precipitation, hail probability, or both  
- Overlay with station location  

---

#### T2.4: SLF Avalanche Bulletin Integration
**Description:** Integrate the SLF (WSL Institute for Snow and Avalanche Research) avalanche bulletin. The bulletin provides danger levels per region (Swiss Alps), updated twice daily.  
**Aufwand:** M (5-7 days)  
**Nutzerwert:** High — Switzerland has the highest avalanche death rate per capita. Critical for Alpine users.  
**Machbarkeit:** Med — SLF provides data via `https://www.slf.ch/` and EnviDat API. Need to map Swiss avalanche regions to user location.  
**Implementation:**  
- Research SLF avalanche bulletin data feed (JSON/XML via EnviDat or whiterisk.ch API)  
- New binary sensor: "Avalanche Warning Active"  
- Sensor with attributes: danger level (1-5), aspect, altitude, region  
- Config flow: select avalanche region or auto-detect from coordinates  

---

#### T2.5: Swiss Natural Hazards Portal Integration
**Description:** Integrate warnings from the Swiss Natural Hazards Portal (natural-hazards.ch / hazardsarden.admin.ch) which aggregates: floods (BAFU), avalanches (SLF), forest fires, storms (MeteoSwiss), earthquakes (SED), and landslides.  
**Aufwand:** M-L (1-2 weeks)  
**Nutzerwert:** High — Unified hazard view for all Swiss natural dangers  
**Machbarkeit:** Med — Need to research the portal's data API (likely REST or Atom feeds)  
**Implementation:**  
- Research hazard portal API endpoints  
- New binary sensors per hazard type  
- Configurable: which hazard types to monitor  
- Attributes: severity, description, valid period, region  

---

#### T2.6: Custom Lovelace Weather Card
**Description:** Build a custom Lovelace card specifically designed for Swiss weather — showing current conditions, MeteoSwiss alerts, pollen levels, foehn index, snow depth, and radar in one unified view.  
**Aufwand:** L (1-2 weeks)  
**Nutzerwert:** High — Transforms the HA UI experience  
**Machbarkeit:** High — Standard HA custom card pattern (Lit Element + TypeScript)  
**Implementation:**  
- New repository: `ha-meteoswiss-card`  
- Show: current temp/condition, 5-day forecast, active alerts (color-coded), pollen strip, foehn indicator, snow depth, AQI  
- Swiss design language (MeteoSwiss color scheme)  
- Configurable: which panels to show  
- Multi-language (de/fr/it/en)  

---

#### T2.7: Granular Options Flow & Sensor Toggle
**Description:** Redesign the options flow to let users enable/disable individual sensors and data sources. Currently everything is all-or-nothing.  
**Aufwand:** M (3-5 days)  
**Nutzerwert:** Med — Reduces clutter for users who only want basic weather  
**Machbarkeit:** Very High — Standard HA options flow pattern  
**Implementation:**  
- Options: toggle snow depth, soil temp, foehn, radiation, AQI, pollen, etc.  
- Forecast days configurable (1-7)  
- Pollen station selection  
- Alert types to monitor  

---

### TIER 3: Vision (Months, game-changing)

---

#### T3.1: MeteoSwiss ICON-CH1 Forecast Model Integration
**Description:** Integrate the MeteoSwiss ICON-CH1-EPS numerical weather prediction model (1km resolution, 33h forecast, updated every 3h). This is the highest-resolution weather model available for Switzerland.  
**Aufwand:** XL (1-2 months)  
**Nutzerwert:** High — 1km resolution >> any other available model for CH  
**Machbarkeit:** Low-Med — Data is GRIB2 format from CSCS object storage. Requires parsing GRIB2 in Python (pygrib/cfgrib), or using pre-processed point extracts. Large data volumes.  
**Implementation:**  
- Research GRIB2 access via `rgw.cscs.ch`  
- Consider point extraction vs grid processing  
- May need pygrib dependency (heavy) or pre-processed NetCDF  
- Ensemble member probabilistic forecasts (rain probability, temp range)  
- Could revolutionize Swiss weather automation  

---

#### T3.2: Full Swiss Environmental Intelligence Platform
**Description:** Transform ha-meteoswiss from a weather integration into a comprehensive Swiss environmental intelligence platform, combining:  
- Weather (current + forecast + ICON model)  
- Air quality (PM, O3, NO2, AQI)  
- Pollen (measured, 13+ types)  
- Radar (precipitation, hail)  
- Avalanche (SLF)  
- Flood (BAFU + GloFAS river discharge)  
- Natural hazards (all Swiss sources)  
- Climate data (heating degree days, evapotranspiration)  
- Phenology (plant development stages)  
- Earthquake (SED)  
- UV radiation  
**Aufwand:** XL (3-6 months)  
**Nutzerwert:** Game-changing — Nothing like this exists in the HA ecosystem  
**Machbarkeit:** Med — All data sources are open and documented, but integration complexity is high  
**USP:** This becomes the **definitive Swiss weather & environment integration** — impossible to replicate for other countries  

---

#### T3.3: Machine Learning Weather Insights
**Description:** Use historical MeteoSwiss NBCN climate data (some stations have 100+ years of data) to provide ML-powered insights:  
- "Today is warmer than 95% of historical equivalents"  
- Anomaly detection (unusual temperature, precipitation patterns)  
- Seasonal predictions based on historical analogs  
- Foehn prediction from pressure gradients  
- Heating/cooling demand forecasting using degree days  
**Aufwand:** XL (2-3 months)  
**Nutzerwert:** Med-High — Unique insights no other integration offers  
**Machbarkeit:** Med — NBCN data is available, ML is feasible with on-device models  
**Implementation:**  
- Fetch NBCN historical data periodically  
- Train simple anomaly detection models  
- Present insights as diagnostic sensors or notifications  

---

#### T3.4: Real-time Precipitation Animation
**Description:** Build a real-time animated precipitation radar using the 5-minute CombiPrecip product, rendered as an overlay on a Swiss map in a Lovelace card.  
**Aufwand:** XL (1-2 months)  
**Nutzerwert:** High — Better than any commercial Swiss weather app  
**Machbarkeit:** Low-Med — Requires processing GRIB2 radar data, rendering animations in browser, high data throughput  
**Implementation:**  
- Background task: fetch 5-min radar frames, cache last 12 (1 hour)  
- Custom Lovelace card: Leaflet/map with radar overlay  
- Animation controls (play/pause/speed)  
- User location marker  

---

## Priority Matrix

```
          HIGH VALUE
              │
  T1.1 Snow   │  T1.7 AQI     T2.1 Pollen    T2.3 Radar
  T1.3 Foehn  │  T1.8 Fcst+   T2.2 MS Fcst   T2.4 Avalanche
  T1.5 i18n   │  T2.5 Hazards T2.6 Card
              │               T3.2 Full Platform
  ────────────┼───────────────
              │
  T1.2 DewPt  │  T1.6 Diag    T2.7 Options
  T1.4 Soil   │               T3.3 ML Insights
              │
          LOW VALUE
  S ←─────────┼───────────→ XL
          EFFORT
```

---

## Recommended Implementation Order

1. **T1.1-T1.4** (Week 1): Snow depth, measured dew point, foehn, soil temp — data already in CSV
2. **T1.5-T1.6** (Week 1): FR/IT translations + diagnostics — quick wins
3. **T1.7-T1.8** (Week 2): Air quality sensors + forecast extensions — extend existing APIs
4. **T2.1** (Week 3-4): MeteoSwiss measured pollen — biggest quality improvement
5. **T2.7** (Week 4): Granular options flow — needed before more sensors
6. **T2.2** (Week 5-6): MeteoSwiss localised forecasting — replace Open-Meteo
7. **T2.3** (Week 7-8): Precipitation radar — high visibility feature
8. **T2.4** (Week 9-10): SLF avalanche bulletin — winter season priority
9. **T2.6** (Week 11-12): Custom Lovelace card — showcase feature
10. **T3.x** (Month 3+): Vision features based on community feedback

---

## Technical Notes

### STAC API Access Pattern (for new collections)
All MeteoSwiss collections follow the same pattern:
1. `GET /api/stac/v1/collections/{collection_id}/items/{station_id}` → STAC Item
2. Item contains `assets` with `{collection_id}_{station}_{granularity}_now.csv`  
3. Download CSV (semicolon-separated), parse latest row

### Pollen Station Codes (16 stations)
PBE (Bern), PBS (Basel), PBU (Buchs SG), PDV (Davos), PGN (Geneva), PLV (Lugano), PLY (Lyss), PLZ (Lucerne), PMA (Maggio), PMH (Münchenstein), PNE (Neuchâtel), PPU (Payerne), PSB (St. Gallen), PSR (Sierre), PVE (Veysonnaz), PZA (Zürich)

### Key API Endpoints (discovered)
- **STAC API:** `https://data.geo.admin.ch/api/stac/v1/`
- **MeteoSwiss App API:** `https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz={plz}00`
- **Open-Meteo Forecast:** `https://api.open-meteo.com/v1/forecast`
- **Open-Meteo Air Quality:** `https://air-quality-api.open-meteo.com/v1/air-quality`
- **Open-Meteo Flood:** `https://flood-api.open-meteo.com/v1/flood`
- **SLF EnviDat:** `https://www.envidat.ch/`
- **BAFU Hydrodaten:** `https://www.hydrodaten.admin.ch/`
- **Swiss Seismological Service:** `http://www.seismo.ethz.ch/`
- **Natural Hazards Portal:** `https://www.natural-hazards.ch/`
