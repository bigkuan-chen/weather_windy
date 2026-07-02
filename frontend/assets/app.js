const state = {
  map: null,
  windyApi: null,
  markerLayer: null,
  labelLayer: null,
  stations: [],
  timer: null,
};

const legendRows = [
  ["< 10 C", "Cold", "#2b6cb0"],
  ["10-15 C", "Cool", "#3182ce"],
  ["15-20 C", "Mild", "#38a169"],
  ["20-25 C", "Comfortable", "#ecc94b"],
  ["25-30 C", "Warm", "#ed8936"],
  ["30-35 C", "Hot", "#e53e3e"],
  ["> 35 C", "Very hot", "#9b2c2c"],
];

const statusEl = document.querySelector("#status");
const refreshButton = document.querySelector("#refreshButton");
const overlaySelect = document.querySelector("#overlaySelect");
const cwaToggle = document.querySelector("#cwaToggle");
const labelToggle = document.querySelector("#labelToggle");
const pointForecastToggle = document.querySelector("#pointForecastToggle");
const countySelect = document.querySelector("#countySelect");
const thresholdInput = document.querySelector("#thresholdInput");
const stationList = document.querySelector("#stationList");
const mapFallback = document.querySelector("#mapFallback");
const mapStatus = document.querySelector("#mapStatus");
const fallbackNote = document.querySelector("#fallbackNote");

const overlayLabels = {
  wind: "Wind",
  temp: "Temperature",
  rain: "Rain",
  clouds: "Clouds",
  pressure: "Pressure",
  waves: "Waves",
  rainAccu: "Rain accumulation",
  snowAccu: "Snow accumulation",
  gust: "Wind gusts",
};

window.addEventListener("error", (event) => {
  setMapStatus(`Browser error: ${event.message}`);
});

window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason?.message || String(event.reason);
  setMapStatus(`Browser error: ${reason}`);
});

function loadStylesheetOnce(id, href) {
  if (document.querySelector(`#${id}`)) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.id = id;
    link.rel = "stylesheet";
    link.href = href;
    link.onload = resolve;
    link.onerror = reject;
    document.head.appendChild(link);
  });
}

function colorByTemperature(temp) {
  if (temp < 10) return "#2b6cb0";
  if (temp < 15) return "#3182ce";
  if (temp < 20) return "#38a169";
  if (temp < 25) return "#ecc94b";
  if (temp < 30) return "#ed8936";
  if (temp < 35) return "#e53e3e";
  return "#9b2c2c";
}

function radiusByTemperature(temp) {
  return Math.max(5, Math.min(12, 5 + (temp - 15) * 0.25));
}

function formatTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-TW", { hour12: false });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderLegend() {
  document.querySelector("#legend").innerHTML = legendRows
    .map(
      ([range, label, color]) => `
        <div class="legend-row">
          <span><span class="swatch" style="display:inline-block;background:${color}"></span> ${range}</span>
          <span>${label}</span>
        </div>
      `
    )
    .join("");
}

function filteredStations() {
  const county = countySelect.value;
  const threshold = Number.parseFloat(thresholdInput.value);
  return state.stations.filter((station) => {
    if (county && station.county !== county) return false;
    if (!Number.isNaN(threshold) && station.temperature_c < threshold) return false;
    return true;
  });
}

function markerPopup(station) {
  const forecastId = `forecast-${station.station_id}`;
  return `
    <strong>${escapeHtml(station.station_name)}</strong><br/>
    ${escapeHtml(station.county || "")} ${escapeHtml(station.town || "")}<br/>
    Temperature: ${station.temperature_c} C<br/>
    Humidity: ${station.humidity_percent ?? "-"}%<br/>
    Wind: ${station.wind_speed_mps ?? "-"} m/s<br/>
    Weather: ${escapeHtml(station.weather || "-")}<br/>
    Time: ${escapeHtml(formatTime(station.observed_at))}
    <div id="${forecastId}" class="forecast-box"></div>
  `;
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(digits);
}

function renderForecastHtml(data, station) {
  const summary = data.summary || {};
  const forecastTemp = summary.temperature_c;
  const diff =
    forecastTemp === null || forecastTemp === undefined
      ? null
      : forecastTemp - station.temperature_c;

  return `
    <hr/>
    <strong>Windy forecast (${escapeHtml(data.model || "gfs")})</strong><br/>
    Forecast time: ${escapeHtml(formatTime(data.forecast_at))}<br/>
    Temperature: ${formatNumber(forecastTemp)} C<br/>
    CWA difference: ${diff === null ? "-" : `${formatNumber(diff, 1)} C`}<br/>
    Humidity: ${formatNumber(summary.humidity_percent, 0)}%<br/>
    Wind: ${formatNumber(summary.wind_speed_mps)} m/s<br/>
    Pressure: ${formatNumber(summary.pressure_hpa, 0)} hPa<br/>
    Precip past 3h: ${formatNumber(summary.precipitation_past3h_mm)} mm
  `;
}

async function loadPointForecast(station) {
  if (!pointForecastToggle.checked) return;

  const forecastEl = document.querySelector(`#forecast-${CSS.escape(station.station_id)}`);
  if (!forecastEl) return;

  forecastEl.innerHTML = '<hr/><span class="muted">Loading Windy forecast...</span>';
  try {
    const params = new URLSearchParams({
      lat: station.lat,
      lon: station.lon,
      model: "gfs",
    });
    const response = await fetch(`/api/windy/point?${params.toString()}`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const data = await response.json();
    forecastEl.innerHTML = renderForecastHtml(data, station);
  } catch (error) {
    forecastEl.innerHTML =
      '<hr/><span class="muted">Windy forecast is unavailable.</span>';
    console.error(error);
  }
}

function renderMarkers() {
  if (!state.map || !state.markerLayer) return;
  state.markerLayer.clearLayers();
  state.labelLayer.clearLayers();

  if (!cwaToggle.checked) return;

  filteredStations().forEach((station) => {
    const color = colorByTemperature(station.temperature_c);
    const marker = L.circleMarker([station.lat, station.lon], {
      radius: radiusByTemperature(station.temperature_c),
      fillColor: color,
      fillOpacity: 0.85,
      color: "#ffffff",
      weight: 1,
    })
      .bindPopup(markerPopup(station));

    marker.on("popupopen", () => loadPointForecast(station));
    marker.addTo(state.markerLayer);

    if (labelToggle.checked && state.map.getZoom() >= 8) {
      L.marker([station.lat, station.lon], {
        interactive: false,
        icon: L.divIcon({
          className: "temp-marker",
          html: `${Math.round(station.temperature_c)} C`,
          iconSize: [42, 16],
          iconAnchor: [21, -4],
        }),
      }).addTo(state.labelLayer);
    }
  });
}

function renderStationList() {
  const rows = filteredStations()
    .slice()
    .sort((a, b) => b.temperature_c - a.temperature_c)
    .slice(0, 80);

  stationList.innerHTML = rows
    .map(
      (station) => `
        <div class="station-row">
          <div>
            <strong>${escapeHtml(station.station_name)}</strong><br/>
            <span>${escapeHtml(station.county || "")} ${escapeHtml(station.town || "")}</span>
          </div>
          <strong>${station.temperature_c} C</strong>
        </div>
      `
    )
    .join("");
}

function renderCountyOptions() {
  const current = countySelect.value;
  const counties = [...new Set(state.stations.map((station) => station.county).filter(Boolean))].sort();
  countySelect.innerHTML = '<option value="">All counties</option>';
  counties.forEach((county) => {
    const option = document.createElement("option");
    option.value = county;
    option.textContent = county;
    countySelect.appendChild(option);
  });
  countySelect.value = counties.includes(current) ? current : "";
}

function setMapStatus(message) {
  mapStatus.textContent = message;
}

async function loadStations(refresh = false) {
  refreshButton.disabled = true;
  statusEl.textContent = "Loading CWA observations...";

  try {
    const response = await fetch(`/api/temperature/latest${refresh ? "?refresh=true" : ""}`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const data = await response.json();
    state.stations = data.stations || [];
    renderCountyOptions();
    renderMarkers();
    renderStationList();
    statusEl.textContent = `Last CWA update: ${formatTime(data.updated_at)} | ${data.count} valid stations`;
  } catch (error) {
    statusEl.textContent = "CWA data is temporarily unavailable.";
    console.error(error);
  } finally {
    refreshButton.disabled = false;
  }
}

async function initFallbackMap(reason = "Windy is unavailable.") {
  if (state.map) return;
  try {
    await loadStylesheetOnce(
      "leaflet-fallback-css",
      "https://unpkg.com/leaflet@1.4.0/dist/leaflet.css"
    );
  } catch (error) {
    console.warn("Unable to load fallback Leaflet CSS", error);
  }
  if (state.map) return;

  mapFallback.hidden = false;
  overlaySelect.disabled = true;
  setMapStatus("Fallback Leaflet map");
  fallbackNote.textContent = `${reason} Showing fallback map.`;
  state.map = L.map("fallbackMap", {
    center: [23.7, 121.0],
    zoom: 7,
    preferCanvas: true,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(state.map);

  state.markerLayer = L.layerGroup().addTo(state.map);
  state.labelLayer = L.layerGroup().addTo(state.map);
  state.map.on("zoomend", renderMarkers);
  renderMarkers();
}

function fillAllowedOverlays(store) {
  let allowed = [];
  try {
    allowed = store.getAllowed("overlay") || [];
  } catch (error) {
    console.warn("Unable to read Windy overlays", error);
  }

  const preferred = ["wind", "temp", "rain", "clouds", "pressure"];
  const values = allowed.length
    ? preferred.filter((value) => allowed.includes(value)).concat(
        allowed.filter((value) => !preferred.includes(value))
      )
    : preferred;

  overlaySelect.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = overlayLabels[value] || value;
    overlaySelect.appendChild(option);
  });

  if (!values.includes("wind")) {
    overlaySelect.value = values[0] || "";
  } else {
    overlaySelect.value = "wind";
  }
}

function setWindyOverlay(value) {
  if (!state.windyApi || !value) return;

  try {
    state.windyApi.store.set("overlay", value);
    window.setTimeout(() => {
      const active = state.windyApi.store.get("overlay");
      overlaySelect.value = active;
      setMapStatus(`Windy layer: ${overlayLabels[active] || active}`);
    }, 100);
  } catch (error) {
    console.error(error);
    setMapStatus(`Windy could not switch to ${value}`);
  }
}

async function initMap() {
  try {
    const response = await fetch("/api/config");
    const config = await response.json();

    if (!config.has_windy_api_key || typeof windyInit !== "function") {
      const reason = !config.has_windy_api_key
        ? "Windy API key is missing."
        : "Windy library did not load.";
      setMapStatus(reason);
      initFallbackMap(reason);
      return;
    }

    setMapStatus("Loading Windy map...");
    const windyTimeout = window.setTimeout(() => {
      if (!state.windyApi) {
        initFallbackMap("Windy initialization timed out.");
      }
    }, 5000);

    windyInit(
      {
        key: config.windy_api_key,
        lat: 23.7,
        lon: 121.0,
        zoom: 7,
        overlay: overlaySelect.value,
        verbose: false,
      },
      (windyApi) => {
        window.clearTimeout(windyTimeout);
        state.windyApi = windyApi;
        state.map = windyApi.map;
        mapFallback.hidden = true;
        overlaySelect.disabled = false;
        fillAllowedOverlays(windyApi.store);
        state.markerLayer = L.layerGroup().addTo(state.map);
        state.labelLayer = L.layerGroup().addTo(state.map);
        setWindyOverlay(overlaySelect.value);
        try {
          windyApi.store.set("particlesAnim", "on");
        } catch (error) {
          console.warn("Unable to enable Windy particles", error);
        }
        if (windyApi.broadcast) {
          windyApi.broadcast.on("redrawFinished", () => {
            const active = windyApi.store.get("overlay");
            setMapStatus(`Windy layer: ${overlayLabels[active] || active}`);
          });
        }
        state.map.on("zoomend", renderMarkers);
        window.setTimeout(() => {
          state.map.invalidateSize();
          const active = windyApi.store.get("overlay");
          setMapStatus(`Windy layer: ${overlayLabels[active] || active}`);
          renderMarkers();
        }, 300);
      }
    );
  } catch (error) {
    console.error(error);
    initFallbackMap("Windy initialization failed.");
  }
}

overlaySelect.addEventListener("change", () => {
  setWindyOverlay(overlaySelect.value);
});
cwaToggle.addEventListener("change", renderMarkers);
labelToggle.addEventListener("change", renderMarkers);
countySelect.addEventListener("change", () => {
  renderMarkers();
  renderStationList();
});
thresholdInput.addEventListener("input", () => {
  renderMarkers();
  renderStationList();
});
refreshButton.addEventListener("click", () => loadStations(true));

renderLegend();
initMap();
loadStations();
state.timer = window.setInterval(() => loadStations(), 5 * 60 * 1000);
