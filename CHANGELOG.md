# Changelog

All notable changes to this project will be documented in this file.

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
