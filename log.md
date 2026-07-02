# Development Log

This log records the full development process for the CWA Windy Temperature Visualization project.

## 1. Initial CWA Data Pipeline

The project started with a request to download CWA OpenData from:

```text
https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0001-001
```

The CWA authorization token was moved into `.env` as:

```env
CWA_TOKEN=...
```

A Python script named `fetch_weather.py` was created to:

- Read the token from `.env`.
- Request the CWA automatic weather station dataset.
- Parse the JSON response.
- Flatten station records.
- Save the cleaned result to `weather.csv`.
- Convert the CSV-style table into SQLite database `weather.db`.

The first successful run produced:

```text
weather.csv
weather.db
874 rows
```

## 2. HTTPS Certificate Handling

The first API request failed with a local Python SSL certificate verification issue. The script was updated to use `certifi` as the certificate authority bundle.

Python 3.14 then rejected part of the certificate chain with:

```text
Missing Subject Key Identifier
```

The SSL context was adjusted by disabling only the strict X.509 verification flag while still keeping certificate and hostname verification enabled.

## 3. Token Handling and Request Method

The endpoint URL was normalized into:

```python
url = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0001-001"
```

An attempt was made to move the CWA token out of the query string by using POST. Several approaches were tested:

- POST with token in form body: returned `401 Unauthorized`.
- POST with token in HTTP header: returned a Windy/CWA WAF-style HTML rejection page.
- GET with token only in HTTP header: returned `400 Bad Request`.

The script was restored to the CWA-supported GET query parameter method while keeping the token in `.env` and out of source code.

`.gitignore` was added to avoid committing:

```text
.env
weather.csv
weather.db
__pycache__/
```

## 4. Database Column Flattening

The first CSV/database version still stored `GeoInfo_Coordinates` as one JSON string column.

The flattening logic was improved so list/dict fields are expanded into separate columns, including:

```text
GeoInfo_Coordinates_TWD67_StationLatitude
GeoInfo_Coordinates_TWD67_StationLongitude
GeoInfo_Coordinates_WGS84_StationLatitude
GeoInfo_Coordinates_WGS84_StationLongitude
```

After regeneration, the SQLite table contained:

```text
874 rows
28 columns
```

## 5. Design Document Implementation

The project then moved from a data script to a web application based on `design.md`.

The first implemented architecture was:

```text
backend/
  app/
    main.py
    config.py
    routers/
    services/
    schemas/

frontend/
  index.html
  assets/
    app.js
    styles.css
```

The backend was implemented with FastAPI and provided:

- CWA data fetching.
- Data normalization.
- Invalid record filtering.
- In-memory cache.
- JSON API endpoints.
- Static frontend serving.

The frontend was implemented with plain HTML, CSS, and JavaScript.

## 6. FastAPI Backend

FastAPI dependencies were added to:

```text
backend/requirements.txt
```

The backend included:

- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/routers/temperature.py`
- `backend/app/routers/health.py`
- `backend/app/services/cwa_client.py`
- `backend/app/services/temperature_service.py`
- `backend/app/services/cache_service.py`
- `backend/app/schemas/temperature.py`

The core endpoint was:

```http
GET /api/temperature/latest
```

Additional endpoints included:

```http
GET /api/temperature/geojson
GET /api/temperature/stations/{station_id}
GET /api/health
```

The backend normalized CWA station data into fields such as:

- `station_id`
- `station_name`
- `county`
- `town`
- `lat`
- `lon`
- `observed_at`
- `temperature_c`
- `humidity_percent`
- `wind_speed_mps`
- `pressure_hpa`

Validation rules removed records with:

- Missing station ID.
- Missing latitude or longitude.
- Invalid observation time.
- Missing or invalid temperature.
- Temperature outside `-20 C` to `50 C`.
- CWA invalid values such as `-99` and `-999`.

The normalized endpoint was verified with about:

```text
826 valid stations
```

The count changed over time as CWA live data updated.

## 7. Initial Frontend

The first frontend rendered:

- Map area.
- Temperature markers.
- Temperature legend.
- Layer controls.
- CWA overlay toggle.
- Station label toggle.
- County filter.
- Minimum temperature filter.
- Station list.
- Manual refresh.
- Auto refresh every 5 minutes.

At first, the frontend used Leaflet with OpenStreetMap/OpenTopoMap because Windy API key handling was still being discussed.

## 8. Windy Map Discussion and Replacement Attempts

The project considered whether Windy had a free API option.

It was confirmed that Windy Map Forecast API has a free testing option but still requires a Map Forecast API key.

The frontend was temporarily changed to use:

```text
Leaflet + OpenStreetMap / OpenTopoMap
```

This removed Windy temporarily and avoided the need for a Windy Map API key.

## 9. Windy Map API Reintroduced

After a Windy Map API key became available, Windy was reimplemented.

The `.env` key names evolved into:

```env
WINDY_MAP_API_KEY=...
WINDY_POINT_API_KEY=...
```

The backend was updated to read:

```python
settings.windy_map_api_key
settings.windy_point_api_key
```

The frontend obtains only the Windy Map key from:

```http
GET /api/config
```

The endpoint returns:

```json
{
  "has_windy_api_key": true,
  "has_windy_map_api_key": true,
  "has_windy_point_api_key": true,
  "windy_api_key": "..."
}
```

The full key is sent to the browser because the Windy Map Forecast API is a browser-side JavaScript API. The CWA token and Windy Point key remain server-side.

## 10. Windy Map Debugging

The Windy map did not display correctly in the main page at first.

Several fixes and diagnostics were added:

- A fallback Leaflet map.
- A map status badge.
- Browser error capture.
- Windy initialization timeout.
- Cache-busting query strings for frontend assets.
- `map.invalidateSize()` after Windy initializes.
- Removal of `leaflet.css` from the main page because Windy documentation says not to load the default Leaflet CSS.

A separate minimal diagnostic page was added:

```http
GET /windy-test
```

This page contains only:

- Leaflet JavaScript.
- Windy `libBoot.js`.
- The Windy map container.
- The Windy Map API key.

`/windy-test` was used to confirm that:

- The Windy key was valid.
- Windy script loading worked.
- The domain/key setup was not the core local issue.

## 11. Main Layout Changed for Windy

The main page was then changed to keep Windy as the fullscreen base map.

The layout became:

```text
Windy map: fullscreen base layer
Top bar: floating overlay
Control panel: floating right-side overlay
CWA markers: Leaflet layer group on the Windy map
```

This avoided the earlier grid layout that could interfere with Windy canvas sizing.

## 12. Windy Layer Selector

The frontend includes a Windy layer selector.

It uses the Windy API store:

```js
windyApi.store.getAllowed("overlay")
windyApi.store.set("overlay", value)
windyApi.store.get("overlay")
```

The visible Windy layer status is shown in the map status badge.

## 13. Windy Point Forecast

Windy Point Forecast was added as an optional popup feature.

The official Point Forecast API format was checked:

```http
POST https://api.windy.com/api/point-forecast/v2
```

The request body includes:

```json
{
  "lat": 24.166144,
  "lon": 121.657414,
  "model": "gfs",
  "parameters": ["temp", "wind", "rh", "pressure", "precip"],
  "levels": ["surface"],
  "key": "WINDY_POINT_API_KEY"
}
```

A backend service was added:

```text
backend/app/services/windy_point_service.py
```

A router was added:

```text
backend/app/routers/windy.py
```

The endpoint is:

```http
GET /api/windy/point?lat={lat}&lon={lon}
```

The frontend has a checkbox:

```text
Windy point forecast
```

When enabled, clicking a CWA station marker loads a Windy forecast for that station coordinate.

Windy raw units were normalized:

```text
K -> C
Pa -> hPa
m -> mm
```

The popup can show:

- Windy forecast model.
- Forecast time.
- Forecast temperature.
- CWA observed vs Windy forecast difference.
- Humidity.
- Wind speed.
- Pressure.
- Past 3-hour precipitation.

## 14. Render Deployment Discussion

The deployment target was discussed.

Vercel was considered but would require frontend/backend adjustment or serverless adaptation.

Streamlit was considered, but the current architecture would not deploy cleanly without changing into a Streamlit single-app model. Streamlit would be better for a pydeck/folium version without Windy Map Forecast API.

Render was selected as the best fit because the current app is:

```text
FastAPI backend + static frontend served by FastAPI
```

Only one Render Web Service is needed.

Render settings:

```text
Service Type: Web Service
Runtime: Python
Build Command: pip install -r backend/requirements.txt
Start Command: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Render environment variables:

```env
CWA_TOKEN=your_cwa_api_key
WINDY_MAP_API_KEY=your_windy_map_forecast_api_key
WINDY_POINT_API_KEY=your_windy_point_forecast_api_key
CACHE_TTL_SECONDS=600
```

## 15. Windy Domain Restrictions

Windy Map API domain restrictions were discussed.

For local and Render deployment, the recommended domain restriction list is:

```text
localhost, 127.0.0.1, weather-windy.onrender.com
```

The project identification can be:

```text
https://weather-windy.onrender.com/
```

The domain restriction should not include:

```text
https://
trailing slash
```

## 16. README Update

The README was updated to include:

- Live Demo URL.
- Feature list.
- Tech stack.
- Architecture.
- Local setup.
- API endpoints.
- Render deployment instructions.
- Windy domain restrictions.
- Data validation rules.
- Security notes.

The live demo URL is:

```text
https://weather-windy.onrender.com
```

No real API keys or tokens were written into README.

## 17. Current Project State

The project currently includes:

```text
backend/
frontend/
fetch_weather.py
README.md
design.md
weather.csv
weather.db
```

The main app entrypoint is:

```text
backend.app.main:app
```

The local development command is:

```powershell
python -m uvicorn backend.app.main:app --reload
```

The Render start command is:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

The app serves:

```http
GET /
GET /windy-test
GET /api/health
GET /api/config
GET /api/debug/config
GET /api/temperature/latest
GET /api/temperature/geojson
GET /api/temperature/stations/{station_id}
GET /api/windy/point?lat={lat}&lon={lon}
```

## 18. Security Summary

Secrets are expected to live in `.env` locally and Render environment variables in production.

Server-side only:

```text
CWA_TOKEN
WINDY_POINT_API_KEY
```

Browser-visible by design:

```text
WINDY_MAP_API_KEY
```

The Windy Map key should be protected using Windy domain restrictions.
