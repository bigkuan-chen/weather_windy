from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.schemas.temperature import StationTemperature


@dataclass
class TemperatureCache:
    stations: list[StationTemperature]
    fetched_at: datetime
    error: str | None = None

    @property
    def latest_cwa_time(self):
        if not self.stations:
            return None
        return max(station.observed_at for station in self.stations)


cache: TemperatureCache | None = None


def get_cache():
    return cache


def set_cache(stations, error=None):
    global cache
    cache = TemperatureCache(
        stations=stations,
        fetched_at=datetime.now(timezone.utc),
        error=error,
    )
    return cache
