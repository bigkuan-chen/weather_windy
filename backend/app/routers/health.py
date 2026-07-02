from fastapi import APIRouter

from backend.app.config import settings
from backend.app.services import cache_service, temperature_service


router = APIRouter(tags=["system"])


@router.get("/api/health")
def health():
    cache = cache_service.get_cache()
    latest_cwa_time = cache.latest_cwa_time if cache else None
    return {
        "status": "ok",
        "cwa_cache_status": "fresh" if temperature_service.is_cache_fresh(cache) else "stale",
        "latest_cwa_time": latest_cwa_time,
        "last_error": cache.error if cache else None,
    }


@router.get("/api/config")
def frontend_config():
    return {
        "has_windy_api_key": bool(settings.windy_map_api_key),
        "has_windy_map_api_key": bool(settings.windy_map_api_key),
        "has_windy_point_api_key": bool(settings.windy_point_api_key),
        "windy_api_key": settings.windy_map_api_key,
    }


@router.get("/api/debug/config")
def debug_config():
    map_key = settings.windy_map_api_key
    point_key = settings.windy_point_api_key
    return {
        "has_windy_map_api_key": bool(map_key),
        "windy_map_api_key_masked": (
            f"{map_key[:4]}...{map_key[-4:]}" if map_key else ""
        ),
        "windy_map_api_key_length": len(map_key),
        "has_windy_point_api_key": bool(point_key),
        "windy_point_api_key_masked": (
            f"{point_key[:4]}...{point_key[-4:]}" if point_key else ""
        ),
        "windy_point_api_key_length": len(point_key),
    }
