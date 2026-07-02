# CWA Temperature Visualization

FastAPI backend and browser frontend for visualizing Taiwan CWA automatic weather station temperatures on a Leaflet map with free public tile layers.

## Setup

1. Install Python dependencies:

   ```powershell
   python -m pip install -r backend/requirements.txt
   ```

2. Keep secrets in `.env` at the project root:

   ```env
   CWA_TOKEN=your_cwa_api_key
   CACHE_TTL_SECONDS=600
   ```

   `CWA_TOKEN` is server-side only and is never sent to the browser.

3. Run the app:

   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```

4. Open:

   ```text
   http://127.0.0.1:8000
   ```

## API

- `GET /api/temperature/latest`
- `GET /api/temperature/latest?refresh=true`
- `GET /api/temperature/geojson`
- `GET /api/temperature/stations/{station_id}`
- `GET /api/health`

## Notes

- The backend caches normalized CWA observations in memory for `CACHE_TTL_SECONDS`.
- Invalid records are filtered out when latitude, longitude, station ID, observation time, or temperature is missing.
- Temperature values outside `-20 C` to `50 C` are ignored.
- The frontend does not use a Windy API key. It uses Leaflet with OpenStreetMap/OpenTopoMap tiles.
