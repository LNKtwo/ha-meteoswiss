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

### 📊 Sensoren
- `sensor.meteoswiss_<station>_temperature` - Aktuelle Temperatur (°C)
- `sensor.meteoswiss_<station>_humidity` - Luftfeuchtigkeit (%)
- `sensor.meteoswiss_<station>_wind_speed` - Windgeschwindigkeit (km/h)
- `sensor.meteoswiss_<station>_wind_direction` - Windrichtung (Grad)
- `sensor.meteoswiss_<station>_precipitation` - Niederschlagsmenge (mm)
- `sensor.meteoswiss_<station>_pressure` - Luftdruck (hPa)

### 🌦️ Open-Meteo API (Forecast)
- Stündlicher Forecast für bis zu 2 Tage
- Täglich aggregierter Forecast
- Kostenloser API (kein API Key nötig)
- Automatische Retries bei Timeouts
- **Dual Source:** Aktuelle Daten von MeteoSwiss, Forecast von Open-Meteo

### 📍 Smart Stationensuche
- Automatische Stationensuche basierend auf PLZ
- Liste aller Stationen im Config Flow
- Kantons-basierte Filterung
- Koordinaten werden automatisch geladen

### 🔧 Konfiguration
- Intuitive Konfiguration über HA UI
- Wahl zwischen MeteoSwiss STAC und Open-Meteo
- Anpassbares Update-Intervall (Standard: 10 Minuten)
- Stationen-Dropdown für einfache Auswahl

### 🎨 Wetter-Icons
- Automatische Anzeige basierend auf Zeit (Tag/Nacht)
- Zustandsabhängige Icons (Sonnig, Bewölkt, Regner, Schneend)
- Wetter-Conditions werden korrekt gemappt

### 🗺️ Stations Map (v3.1.0)
- **Visualisiere alle ~160 MeteoSwiss Stationen auf einer Karte**
- Automatische Koordinaten-Bestimmung aus MeteoSwiss Metadata
- GeoJSON Export für Nutzung mit Map-Tools
- Picture Elements Card Konfiguration für HA Dashboard
- Station-Filter nach Kanton
- Nearby Stations Suche (nächste Stationen zu deinem Standort)
- **Neuer Sensor:** `sensor.meteoswiss_weather_stations` mit allen Stationen-Daten

### 🚀 Intelligentes Caching (v3.2.0)
- **Automatisches Caching für API-Aufrufe** - reduziert API-Last
- **Smart TTL:** Aktuelle Daten (5 min), Forecast (30 min), Stationen (24 Std.)
- **Cache-Statistiken:** Hit-Rate, Misses, Evictions pro Cache
- **Automatische Cache-Invalidierung:** Abgelaufene Einträge werden entfernt
- **Performance-Steigerung:** Weniger API-Calls = schnellere Updates
- **Neuer Sensor:** `sensor.meteoswiss_cache_statistics` mit allen Cache-Daten

### ⚠️ Wetter-Alerts (v3.3.0)
- **MeteoSwiss Wetter-Warnungen** via MeteoSwiss App API
- **Binary Sensoren:** `binary_sensor.meteoswiss_any_alert` und `binary_sensor.meteoswiss_critical_alert`
- **Warn-Level:** 1-5 (von keine bis sehr hohe Gefahr)
- **Warn-Typen:** Gewitter, Regen, Schnee, Wind, Waldbrand, Überschwemmung
- **Gültigkeit:** Gültig von/bis Zeitstempel pro Warnung
- **Outlook-Freigabe:** Vorhersagen werden ignoriert (nur aktive Warnungen)
- **Automatische Updates:** Alle 10 Minuten
- **Attribute:** Anzahl aktiver Warnungen, alle Warnungen mit Details

**HINWEIS:** Diese Funktion nutzt die MeteoSwiss App API. Warnungen sind limitiert auf meteorologische Ereignisse (Gewitter, Regen, Schnee, Wind). Naturgefahren wie Überschwemmungen, Waldbrand, Lawinen werden NICHT übermittelt.

### 🌸 Pollen Integration (NEU! v3.4.1)
- **Schweizer Pollen-Daten** basierend auf MeteoSwiss
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

**Attribute der Pollen-Sensoren:**
- `level` - Pollen-Level (0-4)
- `level_name` - Name des Levels (None, Low, Moderate, High, Very High)
- `value` - Numerischer Wert des Levels
- `is_high_risk` - True bei Level 3+ (Hohes Risiko)
- `active` - True wenn Pollen aktiv (Level > 0)
- `pollen_type` - Typ des Pollens
- `pollen_type_name` - Name des Pollentyps

**Wichtiges zu wissen:**

- **Datenquelle:** Pollen-Daten von MeteoSwiss (offizielle Webseite)
- **Update-Häufigkeit:** Alle 30 Minuten
- **Saisonale Berücksichtigung:** Ausserhalb der Pollen-Saison (Oktober bis März)
- **Caching:** Pollen-Daten werden für 30 Minuten gecachtet

#### Beispiel Automatisierung für Pollen

Erstelle eine Automatisierung für hohe Pollenbelastung:

```yaml
# In automations.yaml
- alias: MeteoSwiss High Pollen Alert
  trigger:
    - platform: numeric_state
      entity_id: sensor.meteoswiss_pollen_birch
      above: 2  # Moderate oder höher
  action:
    - service: notify.mobile_app_my_phone
      data:
        message: "Hohe Birken-Pollenbelastung! Level: {{ states('sensor.meteoswiss_pollen_birch') }}"
```

#### Beispiel Dashboard-Konfiguration für Pollen

```yaml
# In deinem Dashboard
type: entities
entities:
  - entity: sensor.meteoswiss_pollen_birch
    name: Birken-Pollen
    icon: mdi:tree
  - entity: sensor.meteoswiss_pollen_grass
    name: Gräser-Pollen
    icon: mdi:grass
  - entity: sensor.meteoswiss_pollen_ambrosia
    name: Ambrosia-Pollen
    icon: mdi:flower
```

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

#### Methode 1: Picture Elements Card (Einfach)

Nutze die vorbereitete Konfiguration:

```yaml
# In deinem Dashboard (lovelace.yaml oder UI)
type: picture-elements
image: https://i.imgur.com/U5vMxGm.png  # Switzerland map image
elements:
  - type: state-label
    entity: sensor.meteoswiss_weather_stations
    style:
      top: 50%
      left: 50%
      transform: translate(-50%, -50%)
```

Für alle Stationen nutze das `picture_elements_config` Attribut:

```yaml
type: picture-elements
# Kopiere die Konfiguration aus:
# sensor.meteoswiss_weather_stations.attributes.picture_elements_config
```

#### Methode 2: GeoJSON mit Map-Tools

Exportiere die GeoJSON-Daten:

```yaml
# In einem Template Sensor
- platform: template
  sensors:
    stations_geojson:
      value_template: "{{ state_attr('sensor.meteoswiss_weather_stations', 'geojson') | to_json }}"
```

Nutze dies mit:
- **Map Card** von HACS
- **Custom Map** Integrations
- **Leaflet** Integration

#### Methode 3: Nearby Stations Suche

Nutze die API in Automatisierungen:

```yaml
# Beispiel: Finde die nächsten 5 Stationen zu Zürich
service: python_script.nearby_stations
data:
  latitude: 47.3769
  longitude: 8.5417
  max_distance_km: 50
  limit: 5
```

#### Stations nach Kanton filtern

Nutze die `get_stations_by_canton` Funktion:

```python
# In einer Python Script
station_map = hass.states.get('sensor.meteoswiss_weather_stations')
zh_stations = [s for s in station_map.attributes['stations'] if s.get('canton') == 'ZH']
```

#### Beispiel Dashboard-Konfiguration

```yaml
# dashboard.yaml
title: MeteoSwiss Weather Stations
views:
  - title: Switzerland Weather Map
    cards:
      - type: picture-elements
        image: https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Switzerland_location_map.svg/800px-Switzerland_location_map.svg.png
        elements:
          # Automatisch generiert aus picture_elements_config
          # Kopiere aus sensor.meteoswiss_weather_stations.attributes.picture_elements_config
      - type: entities
        entities:
          - sensor.meteoswiss_weather_stations
```

### 🚀 Intelligentes Caching nutzen

Die Integration verwendet automatisch intelligente Caching, um die Performance zu verbessern und API-Calls zu reduzieren.

**Cache-TTL (Time-To-Live):**
- **Aktuelle Wetterdaten:** 5 Minuten (Update-Intervall: 10 min)
- **Forecast-Daten:** 30 Minuten (Update-Intervall: 60 min)
- **Stations-Metadata:** 24 Stunden (ändert sich selten)

#### Cache-Statistiken

Überwache die Cache-Performance mit dem `sensor.meteoswiss_cache_statistics`:

```yaml
# In einem Dashboard
type: entities
entities:
  - sensor.meteoswiss_cache_statistics
```

**Attribute des Sensors:**
- `overall_hit_rate` - Gesamt-Hit-Rate aller Caches (%)
- `current_weather` - Statistiken für aktuelle Wetterdaten
- `forecast` - Statistiken für Forecast-Daten
- `stations` - Statistiken für Stationen-Metadata

**Cache-Statistiken pro Cache:**
- `entries` - Anzahl der Einträge im Cache
- `hits` - Anzahl der Cache-Treffer
- `misses` - Anzahl der Cache-Misses
- `evictions` - Anzahl der automatisch entfernten Einträge
- `hit_rate` - Hit-Rate in %
- `total_requests` - Gesamtanzahl der Requests

#### Cache manuell leeren

Wenn du Daten aktualisieren musst (z.B. nach Änderungen an den Stationen):

```yaml
# Automatisierung zum Leeren aller Caches
- alias: MeteoSwiss Cache leeren
  trigger:
    - platform: time
      at: "03:00:00"
  action:
    - service: python_script.clear_meteoswiss_cache
```

#### Cache-bezogene Logs

Die Caching-Aktivität wird im Log protokolliert:

```
# Cache-Treffer
INFO: Using cached data for station kzrh

# Cache-Miss
INFO: Fetching data for station kzrh

# Cache-Eintrag gesetzt
DEBUG: Cache set: station:kzrh (TTL: 300 sec)

# Cache-Verfall
DEBUG: Cache entry expired: forecast:47.37,8.54
```

#### Performance-Tipps

**Für optimale Performance:**
1. **Update-Intervalle nicht zu klein** - Standardwerte sind bereits optimiert
2. **Cache-Statistiken überwachen** - Eine Hit-Rate > 70% ist gut
3. **Bei Problemen Cache leeren** - Manchmal hilft ein Reset

---

### ⚠️ Wetter-Alerts nutzen (NEU! v3.3.0)

Die Integration erstellt automatisch Binary Sensoren für Wetter-Warnungen.

**Neue Binary Sensoren:**
- `binary_sensor.meteoswiss_any_alert` - Aktiv bei jeder Warnung (Level 2 oder höher)
- `binary_sensor.meteoswiss_critical_alert` - Aktiv bei kritischen Warnungen (Level 3 oder höher)

**Warn-Levels:**
- **Level 1:** Keine oder geringe Gefahr
- **Level 2:** Mässige Gefahr
- **Level 3:** Erhebliche Gefahr
- **Level 4:** Hohe Gefahr
- **Level 5:** Sehr hohe Gefahr

**Warn-Typen:**
- 1 - Gewitter (Thunderstorm)
- 2 - Regen (Rain)
- 3 - Schnee (Snow)
- 4 - Wind (Wind)
- 10 - Waldbrand (Forest Fire)
- 11 - Überschwemmung (Flood)

**Attribute der Sensoren:**
- `active_alerts_count` - Anzahl der aktiven Warnungen
- `alerts` - Liste aller aktiven Warnungen mit Details:
  - `alert_id` - Eindeutige ID der Warnung
  - `warn_type` - Typ der Warnung (Nummer und Name)
  - `warn_type_name` - Name des Warnungstyps
  - `warn_level` - Level der Warnung (1-5)
  - `warn_level_name` - Name des Warnungslevels
  - `title` - Titel der Warnung
  - `description` - Beschreibung der Warnung
  - `valid_from` - Gültig ab (ISO datetime)
  - `valid_to` - Gültig bis (ISO datetime)
  - `outlook` - Ob es eine Vorhersage ist (true/false)

**Zustände:**
- `on` - Warnung aktiv
- `off` - Keine Warnung
- `warning` - Warnung (Level 2)
- `critical` - Kritische Warnung (Level 3+)

#### Beispiel Automatisierung für Wetter-Alerts

Erstelle eine Automatisierung für Warnungen:

```yaml
# In automations.yaml
- alias: MeteoSwiss Critical Warning Alert
  trigger:
    - platform: state
      entity_id: binary_sensor.meteoswiss_critical_alert
      to: "on"
  action:
    - service: notify.mobile_app_my_phone
      data:
        message: "Kritische Wetter-Warnung aktiv! {{ state_attr('binary_sensor.meteoswiss_critical_alert', 'active_alerts_count') }} Warnungen"

- alias: MeteoSwiss All Warning Alert
  trigger:
    - platform: state
      entity_id: binary_sensor.meteoswiss_any_alert
      to: "on"
  action:
    - service: notify.mobile_app_my_phone
      data:
        message: "Wetter-Warnung aktiv! {{ state_attr('binary_sensor.meteoswiss_any_alert', 'alerts') | to_json }}"
```

#### Beispiel Dashboard-Konfiguration für Alerts

```yaml
# In deinem Dashboard
type: entities
entities:
  - entity: binary_sensor.meteoswiss_any_alert
    name: Wetter-Warnung
    icon: mdi:alert
  - entity: binary_sensor.meteoswiss_critical_alert
    name: Kritische Warnung
    icon: mdi:alert-octagram
  - entity: sensor.meteoswiss_weather_stations
    name: Wetterstationen
```

**Wichtiges zu wissen:**

- **Outlook-Freigabe:** Vorhersagen (outlook=true) werden ignoriert. Nur aktive Warnungen lösen den Sensor aus.
- **Gültigkeits-Prüfung:** Warnungen werden automatisch als inaktiv markiert, wenn sie abgelaufen sind (valid_to < now).
- **Update-Intervall:** Warnungen werden alle 10 Minuten von der MeteoSwiss App API abgefragt.
- **Limitation:** Die MeteoSwiss App API liefert nur meteorologische Warnungen (Gewitter, Regen, Schnee, Wind). Naturgefahren wie Überschwemmungen, Waldbrand, Lawinen werden NICHT übermittelt.

---

## 📖 Detaillierte Dokumentation

### Installationsschritte

#### Methode 1: HACS (Empfohlen)

1. Öffne HACS in Home Assistant
2. Gehe zu "Hüpfen und herunterladen"
3. Suche nach "MeteoSwiss" oder "Meteo Swiss"
4. Klicke auf "Download" und dann "Installieren"
5. Warte bis die Installation abgeschlossen ist
6. Führe einen Home Assistant Neustart durch

#### Methode 2: Manuel

1. Klone das Repository:
   ```bash
   cd /path/to/homeassistant/custom_components/
   git clone https://github.com/LNKtwo/ha-meteoswiss.git meteoswiss
   ```
2. Home Assistant Neustart

### Konfigurationsschritte

1. Öffne Home Assistant → Einstellungen → Geräte & Dienste
2. Klicke auf "+ Integration hinzufügen"
3. Suche nach "MeteoSwiss"
4. Wähle Datenquelle:
   - **MeteoSwiss STAC API:** Offizielle MeteoSwiss Stationen (Schweiz)
   - **Open-Meteo API:** Weltweite Wetterdaten
5. Gib deine Postleitzahl ein (z.B. 8001 für Zürich)
6. Wähle eine Wetterstation aus der Dropdown-Liste
7. Setze Update-Intervall (Optional, Standard: 10 Minuten)
8. Klicke auf "Senden"

### Erste Konfiguration

Nach der Installation:

```yaml
# entities.yaml (Optional)
weather:
  - platform: meteoswiss
    name: Zürich Wetter
    postal_code: "8001"
    station_id: "kzrh"
```

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

```yaml
# Forecast in der UI aktivieren
configuration.yaml:
weather:
  - platform: meteoswiss
    postal_code: "8001"
    name: Wetter
    forecast_days: 2
```

**Hinweis:** Der Forecast wird von Open-Meteo API geladen und benötigt eine Internetverbindung.

### Fehler: "Unknown error occurred" beim Einrichten

**Mögliche Ursachen:**
- Postleitzahl enthält ungültige Zeichen
- Keine Verbindung zu MeteoSwiss API
- Home Assistant Version zu alt

**Lösung:**
- Postleitzahl ohne Sonderzeichen eingeben
- Verbindung prüfen
- HA Core auf aktuelle Version aktualisieren (2025.1.0+ empfohlen)

### 504 Gateway Timeout Fehler

**Ursache:** Open-Meteo API ist vorübergehend nicht erreichbar

**Lösung:** Die Integration hat einen automatischen Retry-Mechanismus:
- Max 3 Retries bei Timeouts
- Exponential Backoff (2, 4, 8 Sekunden)
- Fallback zu anderen Datenquellen wenn verfügbar

---

## 🏗️ Technische Details

### API Endpoints

| API | Typ | Zweck | Rate Limit |
|-----|-----|-------|------------|
| MeteoSwiss STAC | Aktuelle Daten | JSON/CSV | Keine Limits |
| Open-Meteo | Forecast | JSON | 10.000 Requests/Tag |

### Update-Intervalle

- **Aktuelle Daten:** 10 Minuten (Standard) - Minimal: 10 Minuten
- **Forecast:** 1 Stunde - Optional: 1-24 Stunden

### Daten-Quellen

**MeteoSwiss STAC API (Aktuelle Daten)**
- URL: https://data.geo.admin.ch/api/stac/v1
- Collection: ch.meteoschweiz.ogd-smn
- Format: JSON STAC Collection
- Stations: ~160 Stationen (A1 Automatic Weather Stations)
- Parameter: Temperatur, Wind, Niederschlag, Luftdruck, Luftfeuchtigkeit
- Update-Häufigkeit: Alle 10 Minuten

**Open-Meteo API (Forecast)**
- URL: https://api.open-meteo.com/v1/forecast
- Typ: Globaler Wetterdienst
- Features: Stündlich + Täglich, 48h Forecast
- Kosten: Kostenlos (kostenlos)
- Authentifizierung: Kein API Key nötig
- Retry-Mechanismus: Automatisch bei Timeouts (Max 3 Retries)
- Timeouts: 30 Sekunden pro Request

### Koordinaten-Logik

**Für MeteoSwiss STAC:**
- Koordinaten werden aus MeteoSwiss Stations-Metadata CSV geladen
- Indizes: lat (Index 14), lon (Index 15)
- Encoding: ISO-8859-1 (mit Umlauten)
- Pro PLZ wird die nächstgelegene Station gewählt

**Für Open-Meteo:**
- Koordinaten werden aus der Konfiguration verwendet (User-Standort)
- Alternativ werden Station-Koordinaten verwendet (wenn MeteoSwiss gewählt)
- Dies stellt sicher, dass der Forecast immer den korrekten Standort anzeigt

### Weather Conditions Mapping

Die Integration mappt Wetterbedingungen auf Home Assistant Weather Conditions:

| WMO Code | Condition | Beschreibung |
|-----------|-----------|-------------|
| 0 | clear-night | Klarer Himmel (Nacht) |
| 1-3 | partlycloudy | Teils bewölkt |
| 45, 48 | fog | Nebel |
| 51-67 | rainy | Regen |
| 71-77 | snowy | Schnee |
| 80-82 | showers | Regenschauer |
| 95-99 | lightning | Gewitter |

**Timezone-Berücksichtigung:**
- Die Condition berücksichtigt die Schweizer Zeitzone (UTC+1)
- Tag: 07:00-08:00 UTC (08:00-09:00 Schweizer)
- Nacht: 20:00-07:00 UTC (21:00-08:00 Schweizer)
- Morgengrau: 07:00-08:00 UTC (wenn kein Regen)

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
INFO: Fetching from MeteoSwiss API for station kzrh
INFO: Successfully updated data for station kzrh
INFO: Fetched forecast from Open-Meteo API
INFO: Forecast coordinator using MeteoSwiss station coordinates: lat=47.37, lon=8.54

# Warnungen
WARNING: Could not load station coordinates
WARNING: Open-Meteo returned 504, retry 1/3
WARNING: Station xyz not found in metadata

# Fehler
ERROR: Failed to fetch station data
ERROR: Error parsing CSV
ERROR: MeteoSwiss API returned 503
```

### Service Calls

```yaml
# Manuelles Update der Integration
service: meteoswiss.update
target:
  entity_id: weather.meteoswiss_kzrh

# Manuelles Neuladen aller Entitäten
service: homeassistant.reload
```

---

## 🎓 Roadmap

### Aktuelle Features (v3.0.0)
- ✅ MeteoSwiss STAC API Integration
- ✅ Open-Meteo Forecast Integration
- ✅ Dual Source Support (MeteoSwiss + Open-Meteo)
- ✅ Smart Stationensuche
- ✅ 5 Sensoren pro Station
- ✅ Weather Entity mit stündlichem Forecast
- ✅ Tages-aggregierter Forecast
- ✅ Retry-Mechanismus für Open-Meteo
- ✅ Timezone-korrekte Conditions (Schweiz)
- ✅ Konfiguration über HA UI

### Geplante Features

- 🔄 Pollen Integration
- 🔄 MeteoSwiss App API (Alternative Datenquelle)
- 🔄 Wetter-Alerts (Schwerwetterwarnungen)
- 🔄 Historische Daten
- 🔄 Karte mit allen Stationen
- 🔄 Optimierter Caching

---

## 📄 Lizenz

MIT License

**Kosten:** Kostenlos

**Datenquellen:**
- MeteoSwiss Open Data (Open Government Data, kostenlos nutzbar)
- Open-Meteo API (Kostenlos, kommerziell frei nutzbar)

---

## 🤝 Contributing

Bug-Reports und Feature-Requests sind willkommen!

- **Issues:** https://github.com/LNKtwo/ha-meteoswiss/issues
- **Pull Requests:** https://github.com/LNKtwo/ha-meteoswiss/pulls

---

## 🏆 Credits

- **Metéo Suisse** (Swiss Federal Office of Meteorology and Climatology)
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

## 📞 Support

- **Issues:** https://github.com/LNKtwo/ha-meteoswiss/issues
- **Discussions:** https://github.com/LNKtwo/ha-meteoswiss/discussions
- **HACS:** https://hacs.xyz/

---

## 🇨🇭 Made in Switzerland

Entwickelt mit ❤️ in Zürich für die Home Assistant Community

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-orange.svg)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-default-blue.svg)](https://hacs.xyz/)
