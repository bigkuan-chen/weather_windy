import json
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi

from backend.app.config import settings


def fetch_cwa_payload():
    if not settings.cwa_api_key:
        raise RuntimeError("CWA_API_KEY or CWA_TOKEN is missing.")

    query = urlencode(
        {
            "Authorization": settings.cwa_api_key,
            "downloadType": "WEB",
            "format": "JSON",
        }
    )
    request = Request(f"{settings.cwa_data_url}?{query}", method="GET")
    context = ssl.create_default_context(cafile=certifi.where())
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT

    with urlopen(request, timeout=30, context=context) as response:
        return json.loads(response.read().decode("utf-8"))
