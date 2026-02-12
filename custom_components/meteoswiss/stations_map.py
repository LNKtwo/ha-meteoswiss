"""MeteoSwiss Stations Map - Display all weather stations on a map."""
from __future__ import annotations

import aiohttp
import json
import logging
from dataclasses import dataclass, asdict
from typing import Final

from .const import STATIONS_METADATA_URL

_LOGGER = logging.getLogger(__name__)


@dataclass
class WeatherStation:
    """Weather station data."""

    station_id: str
    name: str
    latitude: float
    longitude: float
    altitude: float | None = None
    canton: str | None = None
    start_date: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_geojson_feature(self) -> dict:
        """Convert to GeoJSON feature."""
        return {
            "type": "Feature",
            "properties": {
                "station_id": self.station_id,
                "name": self.name,
                "altitude": self.altitude,
                "canton": self.canton,
                "start_date": self.start_date,
            },
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            },
        }


class MeteoSwissStationsMap:
    """MeteoSwiss stations map loader."""

    def __init__(self) -> None:
        """Initialize."""
        self._stations: dict[str, WeatherStation] = {}
        self._loaded = False

    async def load_stations(self) -> dict[str, WeatherStation]:
        """Load all weather stations from MeteoSwiss metadata."""
        if self._loaded:
            return self._stations

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(STATIONS_METADATA_URL) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to load stations: %s", response.status)
                        return {}

                    content_bytes = await response.read()

            # Try different encodings for CSV
            lines = None
            for encoding in ['iso-8859-1', 'latin-1', 'cp1252', 'utf-8-sig', 'utf-8']:
                try:
                    decoded = content_bytes.decode(encoding)
                    lines = decoded.strip().split("\n")
                    if len(lines) > 10:
                        _LOGGER.debug("Successfully decoded CSV with encoding: %s", encoding)
                        break
                except UnicodeDecodeError:
                    continue

            if not lines or len(lines) < 2:
                _LOGGER.error("Failed to decode stations CSV")
                return {}

            # Parse CSV headers
            headers = [h.strip().lower() for h in lines[0].split(";")]

            # Find column indices
            col_id = headers[0] if len(headers) > 0 else "station_id"
            col_name = headers[3] if len(headers) > 3 else "name"
            col_altitude = headers[6] if len(headers) > 6 else None
            col_canton = headers[7] if len(headers) > 7 else None
            col_start = headers[8] if len(headers) > 8 else None

            # Parse CSV rows
            for line in lines[1:]:
                parts = line.split(";")
                if len(parts) > 15:
                    try:
                        station_id = parts[0].strip()
                        name = parts[3].strip() if len(parts) > 3 else station_id
                        lat = float(parts[14]) if parts[14] else None
                        lon = float(parts[15]) if parts[15] else None
                        altitude = float(parts[6]) if parts[6] and col_altitude else None
                        canton = parts[7].strip() if len(parts) > 7 and col_canton else None
                        start_date = parts[8].strip() if len(parts) > 8 and col_start else None

                        if lat and lon:
                            station = WeatherStation(
                                station_id=station_id,
                                name=name,
                                latitude=lat,
                                longitude=lon,
                                altitude=altitude,
                                canton=canton,
                                start_date=start_date,
                            )
                            self._stations[station_id.lower()] = station
                    except (ValueError, TypeError) as e:
                        _LOGGER.debug("Could not parse station: %s - %s", parts[0], e)
                        continue

            self._loaded = True
            _LOGGER.info("Loaded %d weather stations from MeteoSwiss", len(self._stations))
            return self._stations

        except Exception as err:
            _LOGGER.error("Error loading stations: %s", err)
            return {}

    def get_station(self, station_id: str) -> WeatherStation | None:
        """Get a specific station by ID."""
        return self._stations.get(station_id.lower())

    def get_all_stations(self) -> list[WeatherStation]:
        """Get all stations."""
        return list(self._stations.values())

    def get_stations_by_canton(self, canton: str) -> list[WeatherStation]:
        """Get stations by canton."""
        canton_lower = canton.lower()
        return [
            s for s in self._stations.values()
            if s.canton and s.canton.lower() == canton_lower
        ]

    def get_nearby_stations(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 50.0,
        limit: int = 10,
    ) -> list[tuple[WeatherStation, float]]:
        """Get nearby stations sorted by distance."""
        stations_with_distance = []

        for station in self._stations.values():
            distance = self._calculate_distance(
                latitude, longitude,
                station.latitude, station.longitude
            )
            if distance <= max_distance_km:
                stations_with_distance.append((station, distance))

        # Sort by distance and limit
        stations_with_distance.sort(key=lambda x: x[1])
        return stations_with_distance[:limit]

    @staticmethod
    def _calculate_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates (Haversine formula)."""
        from math import radians, cos, sin, asin, sqrt

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in km

        return c * r

    def to_geojson(self) -> dict:
        """Convert all stations to GeoJSON FeatureCollection."""
        features = [station.to_geojson_feature() for station in self._stations.values()]
        return {
            "type": "FeatureCollection",
            "features": features,
        }

    def to_picture_elements_config(self) -> dict:
        """Convert stations to Picture Elements Card configuration."""
        elements = []

        # Normalize coordinates to percentage (0-100)
        # Switzerland bounds roughly: lat 45.8-47.8, lon 5.9-10.5
        min_lat, max_lat = 45.8, 47.8
        min_lon, max_lon = 5.9, 10.5

        for station in self._stations.values():
            # Calculate position
            x = ((station.longitude - min_lon) / (max_lon - min_lon)) * 100
            y = ((station.latitude - min_lat) / (max_lat - min_lat)) * 100

            # Ensure within bounds
            x = max(0, min(100, x))
            y = max(0, min(100, y))

            elements.append({
                "type": "state-label",
                "entity": "sensor.meteoswiss_weather_stations",
                "style": {
                    "top": f"{y}%",
                    "left": f"{x}%",
                    "transform": "translate(-50%, -50%)",
                },
                "title": f"{station.name} ({station.station_id})",
            })

        return {
            "type": "picture-elements",
            "image": "https://i.imgur.com/XYZ.jpg",  # Placeholder for map image
            "elements": elements[:50],  # Limit to 50 elements
        }


# Global instance
_stations_map: MeteoSwissStationsMap | None = None


async def get_stations_map() -> MeteoSwissStationsMap:
    """Get global stations map instance."""
    global _stations_map
    if _stations_map is None:
        _stations_map = MeteoSwissStationsMap()
        await _stations_map.load_stations()
    return _stations_map
