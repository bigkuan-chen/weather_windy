from fastapi import APIRouter

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
