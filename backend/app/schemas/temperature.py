from datetime import datetime

from pydantic import BaseModel


class StationTemperature(BaseModel):
    station_id: str
    station_name: str
    county: str | None = None
    town: str | None = None
    lat: float
    lon: float
    altitude_m: float | None = None
    observed_at: datetime
    temperature_c: float
    humidity_percent: float | None = None
    pressure_hpa: float | None = None
    wind_speed_mps: float | None = None
    wind_direction_deg: float | None = None
    precipitation_mm: float | None = None
    weather: str | None = None


class LatestTemperatureResponse(BaseModel):
    source: str
    updated_at: datetime | None = None
    count: int
    stations: list[StationTemperature]
