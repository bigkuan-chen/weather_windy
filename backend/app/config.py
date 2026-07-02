import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def load_env(path=BASE_DIR / ".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()


class Settings:
    cwa_api_key = os.getenv("CWA_API_KEY") or os.getenv("CWA_TOKEN", "")
    cwa_data_url = os.getenv(
        "CWA_DATA_URL",
        "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0001-001",
    )
    cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "600"))
    windy_map_api_key = (
        os.getenv("WINDY_MAP_API_KEY")
        or os.getenv("WINDY_API_KEY")
        or os.getenv("NEXT_PUBLIC_WINDY_API_KEY", "")
    )
    windy_point_api_key = os.getenv("WINDY_POINT_API_KEY", "")
    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
