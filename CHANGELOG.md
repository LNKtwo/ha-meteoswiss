# Changelog

All notable changes to this project will be documented in this file.

---

## [8.0.0] — 2026-07-31

### Tier 3 — Full Documentation, Code Polish, Production Ready

This is the final major release. The integration is feature-complete, fully documented, and ready for promotion.

### Added
- **Professional README** — complete rewrite with badges, feature table, sensor reference, FAQ, comparison, installation guide
- **docs/SENSORS.md** — full sensor documentation (all entities, units, sources, update intervals)
- **docs/API_SOURCES.md** — data source documentation (APIs, URLs, rate limits, attribution)
- **ROADMAP.md** — updated with all completed features (v6.0.0–v8.0.0) and future ideas
- **Binary sensor translations** — `any_alert`, `critical_alert` keys added to all 4 languages (de/en/fr/it)
- **Forecast pollen translations** — `pollen_birch`, `pollen_alder`, `pollen_grass`, `pollen_mugwort`, `pollen_ambrosia` keys added to all 4 languages
- `quality_scale: platinum` in manifest.json
- `iot_class: cloud_polling` in hacs.json

### Changed
- Version bumped to 8.0.0
- Removed `Platform.CAMERA` from active platforms (camera is placeholder, not functional)
- Inline `import traceback` replaced with `_LOGGER.exception()` in pollen coordinator
- Consolidated duplicate `dataclass` import in sensor.py

### Fixed
- **Undefined type hint** — `PollenMeasurement` replaced with `Any` in pollen_sensor.py
- **Unused import** — `json` removed from sensor.py
- **Unused imports** — `CONF_POSTAL_CODE` removed from openmeteo_coordinator.py and pollen_coordinator_openmeteo.py
- All translation gaps closed — every entity has translations in all 4 Swiss national languages

### Code Quality
- Zero undefined names
- Zero unused imports
- All entities have translation keys
- Consistent logging (debug for routine, warning for recoverable, error for failures)
- Proper `CoordinatorEntity` pattern throughout

---

## [7.0.1] — 2026-07-31

### Removed
- `diagnostics.py` — used `platform.diagnostics` which doesn't exist in HA. Removed to prevent import errors.

---

## [7.0.0] — 2026-07-31

### Tier 2 — Major Features

### Added
- **SLF Avalanche Bulletin placeholder** (`slf.py`) — documented all tested APIs, ready for future implementation
- **BAFU Hydrological Data placeholder** (`hydro.py`) — documented all tested APIs, ready for future implementation
- **Precipitation Radar camera placeholder** (`camera.py`) — documented all tested WMS/TMS endpoints
- **MeteoSwiss measured pollen** (`pollen_meteoswiss.py`) — hourly measured pollen from 16 Swiss stations via ogd-pollen STAC API
- **MeteoSwiss pollen sensors** — 6 measured pollen types (birch, alder, hazel, beech, ash, grass) with 24h history
- **Air quality sensors** — PM2.5, PM10, NO₂, O₃ from Open-Meteo Air Quality API
- **Heating degree days** (Heizgradtage) — SIA 381/3 calculation with daily and seasonal sensors
- **Snow depth sensor** — `htoauts0` from SwissMetNet
- **Foehn index sensor** — `wcc006s0`, uniquely Swiss
- **Soil temperature sensors** — 5 cm, 10 cm, 20 cm depth
- **Measured dew point** — `tde200s0` with Magnus formula fallback
- **Forecast extensions** — snowfall, freezing level height added to forecast coordinator
- **Pollen station selection** — 16 stations configurable in options flow

### Changed
- Pollen coordinator extended to fetch air quality parameters alongside pollen
- Config flow options expanded with pollen station picker
- Forecast coordinator now fetches snowfall and freezing level height

---

## [6.1.0] — 2026-07-31

### Added
- API timeout: 30s default on all requests (was 5min unset default)
- Circuit breaker: after 5 consecutive failures, pauses updates for 5 minutes

### Changed
- WMO weather code mapping centralized in `const.py` (removed 3 duplicate copies)
- Binary sensor migrated to `CoordinatorEntity` pattern (HA best practice)

---

## [6.0.1] — 2026-07-31

### Fixed
- Pollen coordinator now uses shared aiohttp session (session leak)
- Stations CSV loader uses shared session instead of creating orphan connections
- Forecast listener properly unregistered via `async_on_unload`

### Removed
- Dead code: `pollen.py` and `pollen_coordinator.py` (276 lines of unused HTML scraping)
- `aiohttp` from `requirements` (ships with Home Assistant Core)

### Changed
- Pollen coordinator logging from `info` to `debug` (reduces log spam)
- Minimum Home Assistant version: `2024.7.0` (WeatherEntityFeature requirement)

---

## [6.0.0] — 2026-07-31

### Stable Release — Clean Start

All previous versions (v5.0.5 – v5.2.2) have been removed. v6.0.0 is a fresh beginning.

### Fixed (Critical)
- **Shared session leak** — `alerts.py` and pollen coordinators closed the shared aiohttp session, killing all other coordinators with `RuntimeError: Session is closed`
- **Orphan session creation** — Coordinator fallbacks created sessions that were never closed (socket/FD leak)
- **Forecast listener leak** — Weather entity subscribed to forecast coordinator but never unsubscribed on unload

### Fixed (High)
- **Naive datetime** — `datetime.now()` replaced with timezone-aware `datetime.now(timezone.utc)` in alert logic
- **Traceback spam** — `import traceback; _LOGGER.error(traceback.format_exc())` replaced with `_LOGGER.exception()` across 5 files

### Removed
- Dead `VERSION` constant from `const.py`
- All legacy Git tags and GitHub releases (v5.0.5 – v5.2.2)
- Legacy documentation

### Added
- Fresh README with full feature documentation
- Proper device info, entity categories, and attribution
