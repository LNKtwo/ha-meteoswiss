# MeteoSwiss HACS Integration

Home Assistant Custom Integration für MeteoSwiss Open Data API.

## Projekt-Ziel

MeteoSwiss Wetterdaten direkt in Home Assistant integrieren - ohne Drittanbieter, mit offiziellen MeteoSwiss Daten.

## MeteoSwiss Open Data API

**Dokumentation:** https://opendatadocs.meteoswiss.ch

**Terms of Use:** Daten können ohne Einschränkung verwendet werden. Quelle muss angegeben werden ("Source: MeteoSwiss").

### Verfügbare Datensätze

#### A1 - Automatic Weather Stations (Wichtigste)
- **Update:** Alle 10 Minuten
- **Daten:** Temperatur, Wind, Niederschlag, Luftdruck, etc.
- **Standorte:** Automatische Wetterstationen in der ganzen Schweiz
- **Verwendung:** Aktuelle Wetterdaten für Home Assistant Sensoren

#### A7 - Pollen Stations (Optional)
- **Update:** Stündlich/Täglich
- **Daten:** Pollenkonzentrationen für verschiedene Pollenarten
- **Verwendung:** Pollen-Sensoren für Allergie-Warnungen

#### E3 - ICON-CH2 Numerical Weather Model
- **Update:** Alle 6 Stunden
- **Daten:** 120h Vorhersage, 2.1km Grid
- **Verwendung:** Detaillierte Wettervorhersage

#### E4 - Local Forecast
- **Update:** Alle 6 Stunden
- **Daten:** Lokale Vorhersagen, 2km Auflösung
- **Verwendung:** Stündliche Vorhersage für Standort

#### D - Radar Data (Optional)
- **Daten:** Niederschlagsradar & Hagelradar
- **Verwendung:** Regen- & Hagel-Warnungen in Echtzeit

#### C - Climate Data (Optional)
- **Daten:** Homogene Datenreihen & Klimaszenarien CH2025
- **Verwendung:** Langzeit-Klima-Analysen

### API Zugriffsarten

**Aktuell (Stand 2026-02-09):**
- Datei-basierter Download via HTTPS
- Noch keine individual API Queries verfügbar (kommt nach 2026)

**Zukünftig:**
- API Query Endpoint wird für 2026 angekündigt

## Home Assistant Integration Architektur

### Entities

#### Weather Entities
- `weather.meteoswiss_<station>` - Haupt-Wetter-Entity

#### Sensor Entities
- `sensor.meteoswiss_<station>_temperature` - Aktuelle Temperatur
- `sensor.meteoswiss_<station>_humidity` - Luftfeuchtigkeit
- `sensor.meteoswiss_<station>_wind_speed` - Windgeschwindigkeit
- `sensor.meteoswiss_<station>_wind_direction` - Windrichtung
- `sensor.meteoswiss_<station>_precipitation` - Niederschlagsmenge
- `sensor.meteoswiss_<station>_pressure` - Luftdruck

#### Forecast Entities
- `sensor.meteoswiss_<station>_forecast_temp_high` - Höchsttemperatur heute
- `sensor.meteoswiss_<station>_forecast_temp_low` - Tiefsttemperatur heute
- `sensor.meteoswiss_<station>_forecast_condition` - Wettervorhersage (Icon)

#### Pollen Entities (Optional)
- `sensor.meteoswiss_<station>_pollen_birch` - Birkenpollen
- `sensor.meteoswiss_<station>_pollen_grass` - Gräserpollen
- `sensor.meteoswiss_<station>_pollen_ambrosia` - Ambrosiapollen

### Configuration Flow

1. **PLZ eingeben** - Automatische Stationsermittlung
2. **Station auswählen** (falls mehrere in der Nähe)
3. **Update-Intervall einstellen** (Standard: 10min für A1, 6h für Forecast)
4. **Optional: Pollen-Daten aktivieren**
5. **Optional: Radar-Daten aktivieren**

### Dependencies

- `homeassistant` >= 2024.1
- `aiohttp`
- `voluptuous`
- `python-dateutil`

## Projekt-Struktur

```
projects/meteoswiss-hacs/
├── custom_components/
│   └── meteoswiss/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── weather.py
│       ├── translations/
│       └── .translations/
├── docs/
│   ├── PROJECT.md
│   ├── API_REFERENCE.md
│   └── TESTING.md
├── features/
│   └── PROJ-1-feature-*.md
└── src/
    └── prototypes/
```

## Testing

**Test-Standort:** PLZ 6048 (Horw)

**Test-Station:** Finden über MeteoSwiss API

**Test-Szenarien:**
1. [ ] Config Flow durchlaufen
2. [ ] Weather Entity erstellt und funktioniert
3. [ ] Sensoren zeigen korrekte Werte
4. [ ] Forecast wird geladen
5. [ ] Automatische Updates funktionieren
6. [ ] Error Handling bei API-Ausfällen
7. [ ] Logs sind sauber und informativ

## HACS Release

1. GitHub Repository erstellen
2. Tag erstellen (v1.0.0)
3. HACS einreichen: https://hacs.xyz/docs/publish/start
4. Kategorie: Integration
5. Dokumentation bereitstellen

## Credits

- MeteoSwiss Open Data: https://opendatadocs.meteoswiss.ch
- HACS Documentation: https://hacs.xyz/docs/integration/setup
- Home Assistant Developer Docs: https://developers.home-assistant.io/
