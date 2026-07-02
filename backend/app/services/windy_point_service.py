import json
import math
import ssl
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import certifi

from backend.app.config import settings


WINDY_POINT_URL = "https://api.windy.com/api/point-forecast/v2"


def _wind_speed(u, v):
    if u is None or v is None:
        return None
    return math.sqrt((u * u) + (v * v))


def _wind_direction(u, v):
    if u is None or v is None:
        return None
    return (math.degrees(math.atan2(u, v)) + 180) % 360


def _first_number(values):
    if not isinstance(values, list):
        return None
    for value in values:
        if value is not None:
            return value
    return None


def _kelvin_to_celsius(value):
    if value is None:
        return None
    return value - 273.15


def _pa_to_hpa(value):
    if value is None:
        return None
    return value / 100


def _m_to_mm(value):
    if value is None:
        return None
    return value * 1000


def get_point_forecast(lat, lon, model="gfs"):
    if not settings.windy_point_api_key:
        raise RuntimeError("WINDY_POINT_API_KEY is missing.")

    payload = {
        "lat": lat,
        "lon": lon,
        "model": model,
        "parameters": ["temp", "wind", "rh", "pressure", "precip"],
        "levels": ["surface"],
        "key": settings.windy_point_api_key,
    }
    request = Request(
        WINDY_POINT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    context = ssl.create_default_context(cafile=certifi.where())
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT

    with urlopen(request, timeout=30, context=context) as response:
        raw = json.loads(response.read().decode("utf-8"))

    ts = raw.get("ts", [])
    first_index = 0 if ts else None
    first_time = (
        datetime.fromtimestamp(ts[first_index] / 1000, tz=timezone.utc).isoformat()
        if first_index is not None
        else None
    )
    wind_u = _first_number(raw.get("wind_u-surface"))
    wind_v = _first_number(raw.get("wind_v-surface"))
    temperature = _first_number(raw.get("temp-surface"))
    pressure = _first_number(raw.get("pressure-surface"))
    precipitation = _first_number(raw.get("past3hprecip-surface"))

    return {
        "source": "Windy Point Forecast",
        "model": model,
        "lat": lat,
        "lon": lon,
        "forecast_at": first_time,
        "summary": {
            "temperature_c": _kelvin_to_celsius(temperature),
            "humidity_percent": _first_number(raw.get("rh-surface")),
            "pressure_hpa": _pa_to_hpa(pressure),
            "precipitation_past3h_mm": _m_to_mm(precipitation),
            "wind_speed_mps": _wind_speed(wind_u, wind_v),
            "wind_direction_deg": _wind_direction(wind_u, wind_v),
        },
        "units": raw.get("units", {}),
    }
