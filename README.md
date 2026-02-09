# MeteoSwiss Home Assistant Integration

Home Assistant Custom Integration für MeteoSwiss Open Data API.

Offizielle Schweizer Wetterdaten direkt in Home Assistant integrieren.

## Features

- 🌡️ **Aktuelle Wetterdaten** von MeteoSwiss automatischen Wetterstationen (SwissMetNet)
- 📍 **Stationssuche** basierend auf PLZ
- 🔄 **Automatische Updates** (Standard: alle 10 Minuten)
- 📊 **Mehrere Sensoren** für Temperatur, Wind, Regen, Luftfeuchtigkeit, Luftdruck
- 🌦️ **Wetter-Karte** mit Vorhersagen
- 🔐 **Offizielle Daten** direkt von MeteoSwiss (Open Government Data)

## Installation

### HACS Installation

1. HACS öffnen → Integrations → "Hüpfen und herunterladen"
2. Suchen nach "MeteoSwiss" → Download
3. Home Assistant Neustart
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → MeteoSwiss

### Manuelle Installation

1. `custom_components/meteoswiss/` Ordner in dein Home Assistant Verzeichnis kopieren
2. Home Assistant Neustart
3. Integration über das UI hinzufügen

## Konfiguration

1. **PLZ eingeben** (z.B. 6048 für Horw)
2. **Wetterstation auswählen** (Liste der verfügbaren Stationen in der Nähe)
3. **Update-Intervall wählen** (Standard: 10 Minuten, Minimum: 10 Minuten)
4. **Speichern**

## Sensoren

Die Integration erstellt folgende Entities:

### Weather Entity
- `weather.meteoswiss_<station>` - Haupt-Wetter-Entity

### Sensor Entities
- `sensor.meteoswiss_<station>_temperature` - Aktuelle Temperatur (°C)
- `sensor.meteoswiss_<station>_humidity` - Luftfeuchtigkeit (%)
- `sensor.meteoswiss_<station>_wind_speed` - Windgeschwindigkeit (km/h)
- `sensor.meteoswiss_<station>_wind_direction` - Windrichtung (Grad)
- `sensor.meteoswiss_<station>_precipitation` - Niederschlagsmenge (mm)
- `sensor.meteoswiss_<station>_pressure` - Luftdruck (hPa)

## Datenquelle

- **API:** MeteoSwiss Open Data API (STAC)
- **Dokumentation:** https://opendatadocs.meteoswiss.ch
- **Terms of Use:** Daten können ohne Einschränkung verwendet werden. Quelle muss angegeben werden ("Source: MeteoSwiss")

## MeteoSwiss Daten

- **A1 - Automatic Weather Stations:** ~160 Stationen mit vollständigen Messprogramm
- **Update:** Alle 10 Minuten
- **Parameter:** Temperatur, Niederschlag, Wind, Sonnenstrahlung, Luftfeuchtigkeit, Luftdruck

## Support

- **GitHub:** https://github.com/LNKtwo/ha-meteoswiss
- **Issues:** https://github.com/LNKtwo/ha-meteoswiss/issues

## License

MIT License

## Credits

- MeteoSwiss Open Data: https://opendatadocs.meteoswiss.ch
- Home Assistant Developer Docs: https://developers.home-assistant.io/
