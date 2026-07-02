# CWA Windy Temperature Visualization

Live Demo: https://weather-windy.onrender.com

This project visualizes Taiwan CWA automatic weather station observations on top of a Windy weather map. The backend protects server-side API keys, normalizes CWA data, and exposes clean JSON endpoints for the browser map.

## Features

- Windy Map Forecast API weather basemap.
- CWA automatic weather station temperature markers.
- Temperature-based marker colors.
- Station popup with county, town, temperature, humidity, wind, weather, and observation time.
- Optional Windy Point Forecast in station popups.
- CWA observed temperature vs Windy forecast difference.
- Windy layer selector.
- CWA overlay toggle.
- Station label toggle.
- County filter.
- Minimum temperature filter.
- Temperature legend.
- Auto refresh and manual refresh.
- GeoJSON endpoint for map clients.
- Minimal Windy diagnostic page at `/windy-test`.

## Tech Stack

- Backend: Python, FastAPI, Uvicorn, Pydantic
- Frontend: HTML, CSS, JavaScript
- Map: Windy Map Forecast API, Leaflet overlay layers
- Weather observations: Taiwan CWA OpenData
- Forecast lookup: Windy Point Forecast API
- Deployment target: Render Web Service

## Architecture

```text
CWA OpenData
  -> FastAPI backend
  -> normalize, validate, cache
  -> /api/temperature/latest
  -> browser frontend
  -> Windy map + Leaflet CWA marker overlay

Windy Point Forecast API
  -> FastAPI backend only
  -> /api/windy/point
  -> station popup forecast
```

The frontend receives the Windy Map key because the Windy browser map requires it. The CWA token and Windy Point Forecast key stay server-side.

## Local Setup

Install dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Create `.env` in the project root:

```env
CWA_TOKEN=your_cwa_api_key
WINDY_MAP_API_KEY=your_windy_map_forecast_api_key
WINDY_POINT_API_KEY=your_windy_point_forecast_api_key
CACHE_TTL_SECONDS=600
```

Run the app:

```powershell
python -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Windy diagnostic page:

```text
http://127.0.0.1:8000/windy-test
```

## API

- `GET /`
- `GET /windy-test`
- `GET /api/health`
- `GET /api/config`
- `GET /api/debug/config`
- `GET /api/temperature/latest`
- `GET /api/temperature/latest?refresh=true`
- `GET /api/temperature/geojson`
- `GET /api/temperature/stations/{station_id}`
- `GET /api/windy/point?lat={lat}&lon={lon}`

## Render Deployment

Create one Render Web Service. You do not need separate frontend and backend deployments.

Build Command:

```bash
pip install -r backend/requirements.txt
```

Start Command:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Environment Variables:

```env
CWA_TOKEN=your_cwa_api_key
WINDY_MAP_API_KEY=your_windy_map_forecast_api_key
WINDY_POINT_API_KEY=your_windy_point_forecast_api_key
CACHE_TTL_SECONDS=600
```

For Windy Map API domain restrictions, include:

```text
localhost, 127.0.0.1, weather-windy.onrender.com
```

Project identification can be:

```text
https://weather-windy.onrender.com/
```

## Data Validation

The backend removes invalid observations when:

- Station ID is missing.
- Latitude or longitude is missing.
- Observation time is invalid.
- Temperature is missing or not numeric.
- Temperature is outside `-20 C` to `50 C`.
- CWA invalid marker values such as `-99` or `-999` are encountered.

## Security Notes

- Do not commit `.env`.
- `CWA_TOKEN` stays server-side.
- `WINDY_POINT_API_KEY` stays server-side.
- `WINDY_MAP_API_KEY` is browser-visible by design because Windy Map Forecast API runs in the frontend.
- Use Windy domain restrictions to reduce misuse of the map key.
