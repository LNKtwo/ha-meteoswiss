# 🇨🇭 MeteoSwiss — Home Assistant Integration

> Schweizer Wetterdaten direkt aus der Quelle. MeteoSwiss STAC + Open-Meteo + Pollen in einer Integration.

[![GitHub release](https://img.shields.io/github/v/release/LNKtwo/ha-meteoswiss)](https://github.com/LNKtwo/ha-meteoswiss/releases)
[![HA Core](https://img.shields.io/badge/Home%20Assistant-Core-blue)](https://www.home-assistant.io/)
[![License](https://img.shields.io/github/license/LNKtwo/ha-meteoswiss)](LICENSE)

---

## 📋 Inhalt

- [Installation](#-installation)
- [Datenquellen](#-datenquellen)
- [Entitäten](#-entitäten)
- [Configuration & Options Flow](#%EF%B8%8F-configuration--options-flow)
- [Changelog](#-changelog)
- [Troubleshooting](#-troubleshooting)
- [Credits](#-credits)

---

## 🚀 Installation

### Über HACS (empfohlen)

1. HACS → **Integrationen** → **+** → Suche nach **"MeteoSwiss"**
2. **Download** → Warten bis Installation abgeschlossen
3. **Home Assistant neu starten**
4. **Integration hinzufügen:**
   - Einstellungen → Geräte & Dienste → **+ Integration hinzufügen**
   - "MeteoSwiss" suchen
   - Datenquelle wählen (MeteoSwiss STAC oder Open-Meteo)
   - PLZ oder Koordinaten eingeben
   - Station auswählen → Fertig

### Manuell

1. `custom_components/meteoswiss/` nach `/config/custom_components/` kopieren
2. HA neu starten
3. Integration hinzufügen (wie oben)

---

## 📡 Datenquellen

| Quelle | Verwendung | Update-Intervall | API Key |
|---|---|---|---|
| **MeteoSwiss STAC** (data.geo.admin.ch) | Aktuelle Messwerte (~160 Stationen) | 10 Min | Keiner |
| **Open-Meteo** (api.open-meteo.com) | Forecast, Condition, UV-Index | 1 Std | Keiner |
| **Open-Meteo Air Quality** | Pollendaten (Birke, Erle, Gräser, etc.) | 30 Min | Keiner |
| **MeteoSwiss Alerts API** | Unwetterwarnungen | 10 Min | Keiner |

Alle Datenquellen sind kostenlos und benötigen keinen API-Key.

---

## 🌡️ Entitäten

Pro Konfigurations-Eintrag werden folgende Entitäten erstellt:

### Wettersensoren (MeteoSwiss STAC)

| Entität | Beschreibung | Einheit |
|---|---|---|
| Temperature | Lufttemperatur 2m | °C |
| Humidity | Relative Luftfeuchtigkeit | % |
| Wind Speed | Windgeschwindigkeit (10-Min-Mittel) | km/h |
| Wind Direction | Windrichtung | ° |
| Wind Gust | Böenspitze (Sekundenböe) | km/h |
| Pressure | Luftdruck (QFF) | hPa |
| Precipitation | Niederschlag (10-Min-Summe) | mm |
| Dew Point | Taupunkt (berechnet) | °C |
| Sunshine Duration | Sonnenscheindauer (10-Min-Summe) | min |
| Global Radiation | Globalstrahlung | W/m² |

### Open-Meteo Sensoren

| Entität | Beschreibung | Einheit |
|---|---|---|
| UV Index | UV-Index | Index |

### Pollensensoren (Open-Meteo Air Quality)

| Entität | Beschreibung | Einheit |
|---|---|---|
| Birch Pollen | Birkenpollen | grains/m³ |
| Alder Pollen | Erlenpollen | grains/m³ |
| Grass Pollen | Gräserpollen | grains/m³ |
| Mugwort Pollen | Beifußpollen | grains/m³ |
| Ragweed Pollen | Ragweedpollen | grains/m³ |

Level (Low / Moderate / High / Very High) und 24h-Forecast in den Entitäts-Attributen.

### Weather Entity

`weather.meteoswiss_<station>` — Vollwertige Weather Entity mit:
- Aktueller Condition (Sonnig, Bewölkt, Regnerisch, etc.)
- Temperatur, Luftfeuchtigkeit, Wind, Druck
- **Hourly Forecast** (24 Stunden)
- **Daily Forecast** (5 Tage)

### Binary Sensors (Alerts)

| Entität | Beschreibung |
|---|---|
| Weather Alert | Aktive Unwetterwarnung (beliebige Stufe) |
| Critical Weather Alert | Kritische Warnung (Stufe 3+) |

### Diagnostic Entities

| Entität | Beschreibung |
|---|---|
| Stations Map | Verfügbare MeteoSwiss Stationen (JSON) |
| Cache Stats | Cache-Statistiken |

---

## ⚙️ Configuration & Options Flow

### Setup

Beim Hinzufügen der Integration:
1. **Datenquelle wählen:** MeteoSwiss STAC (empfohlen) oder Open-Meteo
2. **PLZ eingeben** (MeteoSwiss) oder **Koordinaten** (Open-Meteo)
3. **Station auswählen** aus der Liste der nächstgelegenen Stationen

### Options Flow (ab v5.1.0)

Einstellungen → Geräte & Dienste → MeteoSwiss → **Konfigurieren**

- **Update-Intervall** anpassbar (Minimum 600 Sekunden)
- Kein Remove + Re-Add mehr nötig

---

## 📖 Changelog

### v5.2.0 (2026-07-03)
- 🔄 **Pollen Sensoren komplett neu geschrieben**
  - Sensor-Keys entsprechen jetzt Open-Meteo API Namen
  - Hazel entfernt (nicht verfügbar), dafür Mugwort (Beifuß)
  - `native_value` numerisch (grains/m³), Level als Attribut
  - 24h Forecast in Attributen
  - Schwellwerte pro Pollentyp

### v5.1.0 – v5.1.7 (2026-07-03)
- ✨ Options Flow: Update-Intervall ohne Neukonfiguration änderbar
- ✨ Windböen-Sensor (Sekundenböe, km/h)
- ✨ Taupunkt-Sensor (Magnus-Formel)
- ✨ Sonnenscheindauer (min) & Globalstrahlung (W/m²)
- ✨ UV-Index von Open-Meteo
- 🔧 Diagnostic Category für Cache/Stations Entities
- 🐛 Pollen Sensoren: diverse Fixes (Imports, Dataclass, Enums, Device Class)
- 🔇 Logging reduziert (~200 INFO → DEBUG)
- 🔗 Session Sharing: Eine aiohttp Session pro Config Entry

### v5.0.7 (2026-07-03)
- 🐛 Daily Forecast (5 Tage) repariert — Coordinator truncierte auf 24h statt 120h

### v5.0.6 (2026-07-03)
- 🔧 Version Sync (const.py → manifest.json)
- 🔇 Logging Cleanup (~200 INFO → DEBUG)
- 🔗 Session Sharing (eine aiohttp Session pro Config Entry)
- 🌤️ WMO Code Mapping: Code 0 respektiert Tag/Nacht
- 🧹 `__init__.py.old` entfernt

### v5.0.5 (2026-02-17)
- Weather Entity Condition Fallback-Kette
- Forecast kompatibel mit HA `weather.get_forecasts` API
- Open-Meteo als Condition-Quelle hinzugefügt

### v4.0.4 (2026-02-13)
- STAC API Migration (data.geo.admin.ch)
- Cache-System mit TTL
- Retry-Mechanismus bei Timeouts

---

## 🔧 Troubleshooting

### Pollen-Sensoren zeigen keinen Wert

- **Ausserhalb der Pollensaison:** Alle Pollenwerte sind 0 → Sensor zeigt `0`
- **API prüfen:** Developer Tools → Service `homeassistant.update_entity` auf einen Pollen-Sensor ausführen
- **Logs aktivieren** (siehe unten)

### HACS zeigt kein Update an

- HACS → Integration → **⋮** → **Update information**
- Repository muss auf `main` branch sein
- `manifest.json` Version muss mit dem Release-Tag übereinstimmen

### Alte Entities nach Update (Entity Registry Cache)

Wenn HA nach einem Update noch alte `device_class` Werte cached:

1. Einstellungen → Geräte & Dienste → **Entitäten**
2. Betroffene Entitäten suchen → **Löschen**
3. Integration **Entfernen** und **neu hinzufügen**
4. Alternativ: HA komplett neu starten

### Logging aktivieren

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.meteoswiss: debug
```

### Forecast testen

```yaml
# Developer Tools → Templates
{{ state_attr('weather.meteoswiss_<station>', 'forecast') }}
```

---

## 📄 Lizenz & Credits

**Lizenz:** MIT

**Datenquellen:**
- [MeteoSwiss](https://www.meteoswiss.admin.ch/) — Open Government Data
- [Open-Meteo](https://open-meteo.com/) — Global Weather API
- [Open-Meteo Air Quality](https://air-quality-api.open-meteo.com/) — Pollen Data

**Autor:** [LNKtwo](https://github.com/LNKtwo)

---

_Keine offizielle MeteoSwiss-Integration. Daten werden über öffentliche APIs bezogen._
