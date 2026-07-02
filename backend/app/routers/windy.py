from fastapi import APIRouter, HTTPException, Query

from backend.app.services import windy_point_service


router = APIRouter(prefix="/api/windy", tags=["windy"])


@router.get("/point")
def get_windy_point_forecast(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    model: str = Query(default="gfs"),
):
    try:
        return windy_point_service.get_point_forecast(lat=lat, lon=lon, model=model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
