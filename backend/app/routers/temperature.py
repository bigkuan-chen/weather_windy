from fastapi import APIRouter, HTTPException, Query

from backend.app.services import temperature_service


router = APIRouter(prefix="/api/temperature", tags=["temperature"])


@router.get("/latest")
def get_latest_temperature(refresh: bool = Query(default=False)):
    return temperature_service.latest_response(force_refresh=refresh)


@router.get("/geojson")
def get_temperature_geojson():
    return temperature_service.geojson_response()


@router.get("/stations/{station_id}")
def get_station_detail(station_id: str):
    station = temperature_service.find_station(station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station
