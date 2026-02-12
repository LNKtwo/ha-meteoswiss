# MeteoSwiss Home Assistant Integration

> **Die ultimative Schweizer Wetter-Integration für Home Assistant**  
> Offizielle MeteoSwiss Daten + Open-Meteo Forecast in einer Integration

---

## 🚀 Quick Start

### Installation

```bash
# HACS Installation
1. HACS öffnen → "Hüpfen und herunterladen"
2. Nach "MeteoSwiss" suchen → Download
3. Home Assistant Neustart
```

### Konfiguration

```yaml
# configuration.yaml
weather:
  - platform: meteoswiss
    name: Wetter Zürich
    postal_code: "8001"
    update_interval: 600  # Optional: 10 Minuten
```

---

## ✨ Features

### 🌡️ MeteoSwiss STAC API (Aktuelle Daten)
- **~160 Automatische Wetterstationen** (SwissMetNet)
- Aktuelle Daten alle 10 Minuten
- Daten direkt von MeteoSwiss (Open Government Data)
- Kein API Key nötig
- **v3.6.0+:** Korrigierte Parameter-IDs für 2025 API Format

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
- **v3.6.1+:** Daily Forecast (Tagesvorschau) jetzt verfügbar
- **Dual Source:** Aktuelle Daten von MeteoSwiss, Forecast von Open-Meteo

### 📍 Smart Stationsuche
- Automatische Stationensuche basierend auf PLZ
- Liste aller Stationen im Config Flow
- Kantons-basierte Filterung
- Koordinaten werden automatisch geladen

### 🧬 Konfiguration
- Intuitive Konfiguration über HA UI
- Wahl zwischen MeteoSwiss STAC und Open-Meteo
- Anpassbares Update-Intervall (Standard: 10 Minuten)
- Stationen-Dropdown für einfache Auswahl

### 🌦️ Wetter-Icons
- Automatische Anzeige basierend auf Zeit (Tag/Nacht)
- Zustandsabhängige Icons (Sonnig, Bewölkt, Regnerisch, Schneidend)
- Wetter-Conditions werden korrekt gemappt

---

## 🗺️ Stations Map (v3.1.0)

**Visualisiere alle ~160 MeteoSwiss Stationen auf einer Karte**

- Automatische Koordinaten-Bestimmung aus MeteoSwiss Metadata
- GeoJSON Export für Nutzung mit Map-Tools
- Picture Elements Card Konfiguration für HA Dashboard
- Station-Filter nach Kanton
- Nearby Stations Suche (nächste Stationen zu deinem Standort)
- **Neuer Sensor:** `sensor.meteoswiss_weather_stations` mit allen Stationen-Daten

---

## 🚀 Intelligentes Caching (v3.2.0)

**Automatisches Caching für API-Aufrufe** - reduziert API-Last

- **Smart TTL:** Aktuelle Daten (5 min), Forecast (30 min), Stationen (24 Std.)
- **Cache-Statistiken:** Hit-Rate, Misses, Evictions pro Cache
- **Automatische Cache-Invalidierung:** Abgelaufene Einträge werden entfernt
- **Performance-Steigerung:** Weniger API-Calls = schnellere Updates
- **Neuer Sensor:** `sensor.meteoswiss_cache_statistics` mit allen Cache-Daten

---

## ⚠️ Wetter-Alerts (v3.3.0)

**MeteoSwiss Wetter-Warnungen** via MeteoSwiss App API

- **Binary Sensoren:** `binary_sensor.meteoswiss_any_alert` und `binary_sensor.meteoswiss_critical_alert`
- **Warn-Level:** 1-5 (von keine bis sehr hohe Gefahr)
- **Warn-Typen:** Gewitter, Regen, Schnee, Wind, Waldbrand, Überschwemmung
- **Gültigkeit:** Gültig von/bis Zeitstempel pro Warnung
- **Outlook-Freigabe:** Vorhersagen werden ignoriert (nur aktive Warnungen)
- **Automatische Updates:** Alle 10 Minuten
- **Attribute:** Anzahl aktiver Warnungen, alle Warnungen mit Details

---

## 🌸 Pollen Integration (v3.4.1+)

**Schweizer Pollen-Daten** basierend auf MeteoSwiss

- **Pollen-Typen:** Birke, Hasel, Erle, Gräser, Ambrosia
- **Update-Intervall:** Alle 30 Minuten
- **Pollen-Level:** 0-4 (Keine, Niedrig, Mässig, Hoch, Sehr hoch)
- **Hohe-Risiko-Prüfung:** Automatische Erkennung bei Level 3 oder höher
- **Neue Sensoren:**
  - `sensor.meteoswiss_pollen_birch` - Birken-Pollen
  - `sensor.meteoswiss_pollen_hazel` - Hasel-Pollen
  - `sensor.meteoswiss_pollen_alder` - Erlen-Pollen
  - `sensor.meteoswiss_pollen_grass` - Gräser-Pollen
  - `sensor.meteoswiss_pollen_ambrosia` - Ambrosia-Pollen

**Hinweis:** Diese Funktion nutzt die MeteoSwiss App API. Warnungen sind limitiert auf meteorologische Ereignisse (Gewitter, Regen, Schnee, Wind). Naturgefahren wie Überschwemmungen, Waldbrand, Lawinen werden NICHT übermittelt.

---

## 🛠️ Behobene Probleme (v3.5.0 bis v3.6.1)

### ✅ v3.5.1 - Missing Import Fix
**Problem:** `NameError: name 'dataclass' is not defined`
**Ursache:** Import von `dataclass` fehlte in `binary_sensor.py`
**Lösung:** `from dataclasses import dataclass` hinzugefügt
**Date:** 2026-02-12

### ✅ v3.5.2 - Timedelta Fix
**Problem:** `AttributeError: 'int' object has no attribute 'total_seconds'`
**Ursache:** `DataUpdateCoordinator` erwartet `timedelta`, nicht `int` (Sekunden)
**Lösung:** `update_interval=timedelta(seconds=update_interval)` Konvertierung
**Date:** 2026-02-12

### ✅ v3.5.3 - Alerts List Format Fix
**Problem:** `'list' object has no attribute 'get'`
**Ursache:** MeteoSwiss App API changed format from dict to list
**Lösung:** Parser refactored to handle both formats
**Date:** 2026-02-12

### ✅ v3.6.0 - MeteoSwiss Parameter IDs Fix
**Problem:** Sensoren zeigen "Unbekannt" (Unknown)
**Ursache:** MeteoSwiss API änderte Parameter-IDs in 2025
**Geänderte IDs:**
- `tre200s0` → `tre005s0` (Temperature)
- `ure200s0` → `xchills0` (Humidity)
- `fu3010z0` → `tde200s0` (Wind Speed)
- `dkl010z0` → `prestas0` (Wind Direction)
- `prestas0` → `pp0qffs0` (Pressure)
**Lösung:** Alle 5 Parameter-IDs aktualisiert
**Date:** 2026-02-12

### ✅ v3.6.1 - Forecast Display Fix
**Problem:** Tagesvorschau wird geladen aber nicht angezeigt
**Ursache:** Weather Entity subscribiert nur auf current weather coordinator
**Lösung:** Forecast-Coordinator Update-Listener hinzugefügt
**Date:** 2026-02-12

---

## 📖 Detaillierte Dokumentation

### 🗺️ Stations Map nutzen

Die Integration stellt automatisch einen neuen Sensor zur Verfügung:
- `sensor.meteoswiss_weather_stations` - Zeigt die Anzahl aller Stationen an

**Attribute des Sensors:**
- `station_count` - Anzahl aller geladenen Stationen
- `stations` - Liste der Stationen (begrenzt auf erste 20)
- `geojson` - GeoJSON FeatureCollection mit allen Stationen
- `picture_elements_config` - Vorkonfigurierte Picture Elements Card

---

## 🛠️ Troubleshooting

### Sensoren zeigen keine Daten an

```bash
# Home Assistant Logs prüfen
/homeassistant/home-assistant.log | grep -i meteoswiss

# Logs in der HA UI prüfen
Entwickler-Werkzeuge → YAML → MeteoSwiss
```

**Mögliche Lösungen:**
- Home Assistant Neustart
- Integration neu konfigurieren
- Aktualisierung erzwingen:
  ```yaml
    service: meteoswiss.update
    target:
      entity_id: weather.meteoswiss_kzrh
  ```

### Forecast wird nicht angezeigt

**Prüfe:**
1. Weather Entity geladen?
2. Forecast-Daten verfügbar?
3. Debug-Logs aktivieren:
  ```yaml
  logger:
    custom_components.meteoswiss: debug
  ```

---

## 🏗️ Technische Details

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
- Timeouts: 30 Sekunden pro Request

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

### Log-Meldungen

```
# Normale Operation
INFO: Fetching from MeteoSwiss API for station luz
INFO: Using cached Open-Meteo data
INFO: Successfully updated Open-Meteo data

# Warnungen
WARNING: Could not load station coordinates
WARNING: Open-Meteo returned 504, retry 1/3
WARNING: Station xyz not found in metadata

# Fehler
ERROR: Failed to fetch station data
ERROR: Error parsing CSV
ERROR: MeteoSwiss API returned 503
```

---

## 📄 Changelog

### v3.6.1 (2026-02-12)
- ✅ Fix: Tagesvorschau wird nicht angezeigt
- ✅ Verbessert: Forecast-Coordinator Update Listener

### v3.6.0 (2026-02-12)
- ✅ Fix: MeteoSwiss Parameter-IDs (2025 API Format)
- ✅ Alle 5 Parameter-IDs korrigiert
- ✅ Sensors zeigen jetzt wieder Werte

### v3.5.3 (2026-02-12)
- ✅ Fix: Alerts List Format (Dict → List)
- ✅ Parser jetzt kompatibel mit API-Änderung

### v3.5.2 (2026-02-12)
- ✅ Fix: Timedelta Konvertierung
- ✅ `DataUpdateCoordinator` Kompatibilität

### v3.5.1 (2026-02-12)
- ✅ Fix: Missing `dataclass` import
- ✅ Binary Sensor Fehler behoben

### v3.5.0 (2026-02-11)
- ✅ Release: Feature Freeze und Stabilisierung
- ✅ Alle v3.x Features integriert

### v3.4.1 (2026-02-12)
- ✅ Fix: Import Konflikt bei Pollen Integration
- ✅ Namensräumung korrigiert

### v3.4.0 (2026-02-12)
- ✅ Feature: Pollen Integration
- ✅ 4 Pollen-Typen implementiert

### v3.3.0 (2026-02-12)
- ✅ Feature: Wetter-Alerts via MeteoSwiss App API
- ✅ Binary Sensoren für Warnungen
- ✅ Warn-Level und -Typen

### v3.2.0 (2026-02-12)
- ✅ Feature: Intelligentes Caching
- ✅ Cache-Statistiken Sensor
- ✅ Performance-Steigerung

### v3.1.0 (2026-02-12)
- ✅ Feature: Stations Map
- ✅ Visualisierung aller Stationen
- ✅ GeoJSON Export

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

- **Original Code**
  - https://github.com/LNKtwo/ha-meteoswiss

---

## 🏞 Support

- **Issues:** https://github.com/LNKtwo/ha-meteoswiss/issues
- **Discussions:** https://github.com/LNKtwo/ha-meteoswiss/discussions
- **HACS:** https://hacs.xyz/

---

## 🇨🇭 Made in Switzerland

Entwickelt mit ❤️ in Zürich für die Home Assistant Community

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-orange.svg)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-default-blue.svg)](https://hacs.xyz/)
