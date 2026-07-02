from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.schemas.temperature import LatestTemperatureResponse, StationTemperature
from backend.app.services import cache_service, cwa_client


INVALID_VALUES = {"", "X", "NA", "N/A", "null", "None", None, "-99", "-999"}


def parse_float(value):
    if value in INVALID_VALUES:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_datetime(value):
    if value in INVALID_VALUES:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def is_cache_fresh(cache):
    if cache is None:
        return False
    age = datetime.now(timezone.utc) - cache.fetched_at
    return age.total_seconds() < settings.cache_ttl_seconds


def get_stations(payload):
    stations = payload.get("cwaopendata", {}).get("dataset", {}).get("Station", [])
    if isinstance(stations, dict):
        return [stations]
    return stations


def get_coordinate(geo_info, preferred_name="WGS84"):
    coordinates = geo_info.get("Coordinates", [])
    if isinstance(coordinates, dict):
        coordinates = [coordinates]

    selected = None
    for coordinate in coordinates:
        if coordinate.get("CoordinateName") == preferred_name:
            selected = coordinate
            break
    if selected is None and coordinates:
        selected = coordinates[0]
    if not selected:
        return None, None
    return parse_float(selected.get("StationLatitude")), parse_float(
        selected.get("StationLongitude")
    )


def normalize_station(raw_station):
    geo_info = raw_station.get("GeoInfo", {})
    weather_element = raw_station.get("WeatherElement", {})
    obs_time = raw_station.get("ObsTime", {})
    now = weather_element.get("Now", {})

    lat, lon = get_coordinate(geo_info)
    temperature = parse_float(weather_element.get("AirTemperature"))
    observed_at = parse_datetime(obs_time.get("DateTime"))
    station_id = raw_station.get("StationId")

    if not station_id or lat is None or lon is None:
        return None
    if temperature is None or temperature < -20 or temperature > 50:
        return None
    if observed_at is None:
        return None

    return StationTemperature(
        station_id=str(station_id),
        station_name=str(raw_station.get("StationName") or station_id),
        county=geo_info.get("CountyName"),
        town=geo_info.get("TownName"),
        lat=lat,
        lon=lon,
        altitude_m=parse_float(geo_info.get("StationAltitude")),
        observed_at=observed_at,
        temperature_c=temperature,
        humidity_percent=parse_float(weather_element.get("RelativeHumidity")),
        pressure_hpa=parse_float(weather_element.get("AirPressure")),
        wind_speed_mps=parse_float(weather_element.get("WindSpeed")),
        wind_direction_deg=parse_float(weather_element.get("WindDirection")),
        precipitation_mm=parse_float(now.get("Precipitation")),
        weather=weather_element.get("Weather"),
    )


def load_latest(force_refresh=False):
    cached = cache_service.get_cache()
    if not force_refresh and is_cache_fresh(cached):
        return cached

    try:
        payload = cwa_client.fetch_cwa_payload()
        stations = [
            station
            for station in (normalize_station(raw) for raw in get_stations(payload))
            if station is not None
        ]
        return cache_service.set_cache(stations)
    except Exception as exc:
        if cached:
            cached.error = str(exc)
            return cached
        raise


def latest_response(force_refresh=False):
    cache = load_latest(force_refresh=force_refresh)
    return LatestTemperatureResponse(
        source="CWA",
        updated_at=cache.latest_cwa_time,
        count=len(cache.stations),
        stations=cache.stations,
    )


def find_station(station_id):
    cache = load_latest()
    for station in cache.stations:
        if station.station_id == station_id:
            return station
    return None


def geojson_response():
    cache = load_latest()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [station.lon, station.lat],
                },
                "properties": {
                    "station_id": station.station_id,
                    "station_name": station.station_name,
                    "county": station.county,
                    "town": station.town,
                    "observed_at": station.observed_at.isoformat(),
                    "temperature_c": station.temperature_c,
                    "humidity_percent": station.humidity_percent,
                    "wind_speed_mps": station.wind_speed_mps,
                    "weather": station.weather,
                },
            }
            for station in cache.stations
        ],
    }
