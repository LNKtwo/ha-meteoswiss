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

2. **Relevante Logzeilen prüfen:**
   ```
   INFO: WeatherEntity initialized - lat/lon: 47.37/8.54
   INFO: MeteoSwiss coordinator data: {temperature: 15.5, ...}
   INFO: Forecast coordinator data (count): 120
   INFO: ✅ Condition resolved via Open-Meteo: partlycloudy (code: 2)
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
# Normale Operation
INFO: WeatherEntity initialized - lat/lon: 47.37/8.54
INFO: MeteoSwiss coordinator data: {temperature: 15.5, humidity: 65, ...}
INFO: Forecast coordinator data (count): 120
INFO: ✅ Condition resolved via Open-Meteo: partlycloudy (code: 2)

# Warnungen (erwartet)
WARNING: Using safe fallback condition: partlycloudy (no condition source available)
WARNING: Forecast coordinator data (count): 0

# Fehler (kritisch)
ERROR: Failed to fetch station data
ERROR: No condition data available, returning None
ERROR: Open-Meteo API timeout after retries
```

---

## 📄 Changelog

### v4.0.5 (2026-02-16)
- ✅ Fix: Weather entity condition no longer stuck at 'unknown' when data exists
- ✅ Feature: Fallback chain (Open-Meteo current → MeteoSwiss symbol → numeric safe fallback)
- ✅ Feature: Forecast compatible with modern HA (async_forecast_hourly/async_forecast_daily)
- ✅ Add: WMO weather code mapping for Open-Meteo
- ✅ Add: MeteoSwiss symbol mapping
- ✅ Add: Enhanced debug logging for troubleshooting
- ✅ Fix: Unreachable code bug in coordinator data access
- ✅ Improve: Error handling in forecast methods
- ✅ Note: No breaking changes

### v4.0.4 (2026-02-13)
- ✅ Fix: UnboundLocalError for lat/lon in OpenMeteo data source
- ✅ Fix: Retry decorator was async (TypeError: coroutine not callable)
- ✅ Add: Remove __pycache__, add hacs.json

### v4.0.3 (2026-02-13)
- ✅ Release: v4.0.1

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
