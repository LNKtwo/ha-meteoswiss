# MeteoSwiss Home Assistant Integration

> **Die ultimative Schweizer Wetter-Integration für Home Assistant**
> Offizielle MeteoSwiss Daten + Open-Meteo Forecast in einer Integration

---

## 🚀 Quick Start

### Installation (HACS)

1. **HACS öffnen** → "Hüpfen und herunterladen"
2. Nach **"MeteoSwiss"** suchen → Download
3. **Home Assistant Neustart**
4. **Integration hinzufügen:**
   - Einstellungen → Geräte & Dienste → + Integration hinzufügen
   - "MeteoSwiss" auswählen
   - PLZ/Standort eingeben → Station auswählen
   - Fertig!

⚠️ **YAML-Konfiguration ist nicht mehr erforderlich.** Nutze den Config Flow über die UI.

---

## ✨ Features

### 🌡️ MeteoSwiss STAC API (Aktuelle Daten)
- **~160 Automatische Wetterstationen** (SwissMetNet)
- Aktuelle Daten alle 10 Minuten
- Daten direkt von MeteoSwiss (Open Government Data)
- Kein API Key nötig
- **v4.0.5+:** Weather Entity Condition Fallback-Kette (kein "unknown" mehr)

### 🌦️ Weather Entity
- `weather.meteoswiss_<station>` - Vollständiges Wetter-Entity
- Aktuelle Condition (Sonnig, Bewölkt, Regnerisch, etc.)
- Temperatur, Luftfeuchtigkeit, Wind, Niederschlag
- **Hourly Forecast** (bis zu 24 Stunden)
- **Daily Forecast** (bis zu 5 Tage)
- **v4.0.5+:** Robuste Condition-Auflösung (Open-Meteo → MeteoSwiss → Fallback)
- **v4.0.5+:** Forecast kompatibel mit moderner HA API (`weather.get_forecasts`)

### 📊 Sensoren
- `sensor.meteoswiss_<station>_temperature` - Aktuelle Temperatur (°C)
- `sensor.meteoswiss_<station>_humidity` - Luftfeuchtigkeit (%)
- `sensor.meteoswiss_<station>_wind_speed` - Windgeschwindigkeit (km/h)
- `sensor.meteoswiss_<station>_wind_direction` - Windrichtung (Grad)
- `sensor.meteoswiss_<station>_precipitation` - Niederschlagsmenge (mm)
- `sensor.meteoswiss_<station>_pressure` - Luftdruck (hPa)

### 📈 Open-Meteo API (Forecast)
- Stündlicher Forecast für bis zu 2 Tage
- Täglich aggregierter Forecast (7 Tage)
- Kostenloser API (kein API Key nötig)
- Automatische Retries bei Timeouts
- **Dual Source:** Aktuelle Daten von MeteoSwiss, Forecast von Open-Meteo

### 📍 Smart Stationsuche
- Automatische Stationensuche basierend auf PLZ
- Liste aller Stationen im Config Flow
- Kantons-basierte Filterung
- Koordinaten werden automatisch geladen

---

## 🛠️ Troubleshooting

### Weather Entity zeigt "unknown"

**Symptom:** `weather.meteoswiss_<station>` bleibt im Zustand "unknown"

**Ursachen & Lösungen:**

1. **Debug-Logging aktivieren:**
   ```yaml
   logger:
     logs:
       custom_components.meteoswiss: debug
   ```

2. **Relevante Logzeilen prüfen (DEBUG):**
   ```
   DEBUG: Fetching data for station KZRH
   DEBUG: Condition resolved via Open-Meteo: partlycloudy (code: 2)
   ```

3. **Fallback-Kette prüfen:**
   - Open-Meteo Current (Priority 1)
   - MeteoSwiss Symbol/Icon (Priority 2)
   - Niederschlag/Zeit-Fallback (Priority 3)
   - Safe Fallback "partlycloudy" (Priority 4)
   - Nur None wenn absolut keine Daten

4. **Manuelles Update erzwingen:**
   ```yaml
   service: homeassistant.update_entity
   target:
     entity_id: weather.meteoswiss_kzrh
   ```

### Forecast wird nicht angezeigt

**Prüfe:**
1. Weather Entity geladen? (`weather.meteoswiss_<station>`)
2. Forecast-Daten verfügbar? (Logs prüfen)
3. **Tester in HA Developer Tools:**
   ```yaml
   {{ state_attr('weather.meteoswiss_kzrh', 'forecast') }}
   ```

### Keine Kollision mit `weather.openmeteo_*`

**Wichtig:** Diese Integration erstellt KEINE Entities in der `openmeteo` Domain.

- MeteoSwiss Weather Entity: `weather.meteoswiss_<station>`
- Externe Open-Meteo Integration: `weather.openmeteo_<location>`
- Beide können parallel existieren ohne Konflikte

**Interne Open-Meteo Nutzung:**
- Nur für Forecast-Daten
- Isoliert von externer Integration
- Kein API Key erforderlich

---

## 📖 Detaillierte Dokumentation

### Datenquellen

**MeteoSwiss STAC API (Aktuelle Daten)**
- URL: https://data.geo.admin.ch/api/stac/v1
- Collection: ch.meteoschweiz.ogd-smn
- Format: JSON STAC Collection
- Stations: ~160 Stationen (SwissMetNet)
- Parameter: Temperatur, Wind, Niederschlag, Luftdruck, Luftfeuchtigkeit
- Update-Häufigkeit: Alle 10 Minuten

**Open-Meteo API (Forecast)**
- URL: https://api.open-meteo.com/v1/forecast
- Typ: Globaler Wetterdienst
- Features: Stündlich + Täglich, 48h Forecast
- Kosten: Kostenlos (kostenlos nutzbar)
- Authentifizierung: Kein API Key nötig
- Retry-Mechanismus: Automatisch bei Timeouts (Max 3 Retries)

---

## 🔨 Debugging

### Logging aktivieren

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.meteoswiss: debug
```

### Wichtige Log-Meldungen

```
# Normale Operation (DEBUG)
DEBUG: Fetching data for station KZRH
DEBUG: Successfully parsed data: {temperature: 15.5, ...}
DEBUG: Condition resolved via Open-Meteo: partlycloudy (code: 2)

# Fehler (kritisch)
ERROR: Failed to fetch station data
ERROR: Open-Meteo API timeout after retries
```

---

## 📄 Changelog

### v5.1.0 (2026-07-03)
- ✨ **Options Flow:** Update-Intervall ändern ohne Neukonfiguration
- ✨ **Windböen-Sensor:** Böenspitze (Sekundenböe, km/h) von MeteoSwiss
- ✨ **Taupunkt-Sensor:** Berechnet aus Temp + Luftfeuchte (Magnus-Formel)
- ✨ **Sonnenscheindauer:** 10-Minuten-Summe (min) von MeteoSwiss
- ✨ **Globalstrahlung:** 10-Minuten-Mittel (W/m²) von MeteoSwiss
- ✨ **UV-Index:** Von Open-Meteo API
- 🔧 **Diagnostic Category:** Cache-Stats und Stations-Map als Diagnostic-Entities
- 🌐 Übersetzungen DE/EN aktualisiert

### v5.0.7 (2026-07-03)
- 🐛 **FIXED:** Daily Forecast (5 Tage) wurde nicht angezeigt
- Forecast-Coordinator hat Daten auf 24h abgeschnitten statt 120h (5 Tage)
- `min(24, ...)` → `min(120, ...)` in forecast_coordinator.py

### v5.0.6 (2026-07-03)
- 🔧 Version sync: const.py 4.0.4 → 5.0.5
- 🧹 Entfernt: `__init__.py.old`
- 🔇 Logging reduziert: ~200 INFO → DEBUG (saubere HA Logs)
- 🔗 Session Sharing: Eine gemeinsame aiohttp Session pro Config Entry
- 🌤️ WMO Code Mapping: Code 0 respektiert Tag/Nacht, Duplikate entfernt
- 🧹 Weather Entity: Property-Methoden aufgeräumt, keine Warning-Spam mehr

### v5.0.5 (2026-02-17) - FINAL
- ✅ **FIXED:** Weather Entity attributes (temperature, humidity, pressure, wind) showing null
- ✅ **FIXED:** AttributeError: 'MeteoSwissWeather' object has no attribute '_station_name'
- ✅ **FIXED:** coordinator.data Property wrapper causing data loss
- ✅ **FIXED:** Weather Entity reads directly from coordinator.data
- ✅ **FIXED:** Added comprehensive logging for debugging
- ✅ All known issues resolved - stable release

### v5.0.0 (2026-02-16)
- ✅ Feature: Forecast compatible with modern HA (async_forecast_hourly/async_forecast_daily)
- ✅ Feature: Fallback chain (Open-Meteo current → MeteoSwiss symbol → numeric safe fallback)
- ✅ Add: WMO weather code mapping for Open-Meteo
- ✅ Add: MeteoSwiss symbol mapping
- ✅ Add: Enhanced debug logging for troubleshooting
- ✅ Fix: Unreachable code bug in coordinator data access
- ✅ Improve: Error handling in forecast methods

### v4.0.0 (2026-02-13)
- ✅ Feature: MeteoSwiss STAC API integration (SwissMetNet)
- ✅ Feature: Open-Meteo Forecast API integration
- ✅ Feature: ~160 automatic weather stations
- ✅ Feature: 10-minute update interval for current weather
- ✅ Feature: Hourly forecast (24 hours)
- ✅ Feature: Daily forecast (5 days)
- ✅ Feature: Smart station search based on postal code
- ✅ Feature: Dual source (MeteoSwiss + Open-Meteo)
- ✅ No API key required

---

## 📄 Lizenz

MIT License

**Kosten:** Kostenlos

**Datenquellen:**
- MeteoSwiss Open Data (Open Government Data, kostenlos nutzbar)
- Open-Meteo API (kostenlos kommerziell frei nutzbar)

---

## 🤝 Contributing

Bug-Reports und Feature-Requests sind willkommen!

- **Issues:** https://github.com/LNKtwo/ha-meteoswiss/issues
- **Pull Requests:** https://github.com/LNKtwo/ha-meteoswiss/pulls

---

## 🏆 Credits

- **Météo Suisse** (Swiss Federal Office of Meteorology and Climatology)
  - Offizielle Schweizer Wetterdaten
  - Open Government Data Initiative
  - https://opendata.swiss/de/

- **Open-Meteo**
  - Kostenlose Wetter-API
  - https://open-meteo.com/

- **Home Assistant**
  - https://www.home-assistant.io/

---

## 🏞 Support

- **Issues:** https://github.com/LNKtwo/ha-meteoswiss/issues
- **Discussions:** https://github.com/LNKtwo/ha-meteoswiss/discussions
- **HACS:** https://hacs.xyz/

---

## 🇨🇭 Made in Switzerland

Entwickelt mit ❤️ in Zürich für die Home Assistant Community

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-orange.svg)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Default-blue.svg)](https://hacs.xyz/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
