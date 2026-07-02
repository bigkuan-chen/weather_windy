const state = {
  map: null,
  markerLayer: null,
  labelLayer: null,
  baseLayers: {},
  activeBaseLayer: null,
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
const baseMapSelect = document.querySelector("#baseMapSelect");
const cwaToggle = document.querySelector("#cwaToggle");
const labelToggle = document.querySelector("#labelToggle");
const countySelect = document.querySelector("#countySelect");
const thresholdInput = document.querySelector("#thresholdInput");
const stationList = document.querySelector("#stationList");

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
  return `
    <strong>${escapeHtml(station.station_name)}</strong><br/>
    ${escapeHtml(station.county || "")} ${escapeHtml(station.town || "")}<br/>
    Temperature: ${station.temperature_c} C<br/>
    Humidity: ${station.humidity_percent ?? "-"}%<br/>
    Wind: ${station.wind_speed_mps ?? "-"} m/s<br/>
    Weather: ${escapeHtml(station.weather || "-")}<br/>
    Time: ${escapeHtml(formatTime(station.observed_at))}
  `;
}

function renderMarkers() {
  if (!state.map || !state.markerLayer) return;
  state.markerLayer.clearLayers();
  state.labelLayer.clearLayers();

  if (!cwaToggle.checked) return;

  filteredStations().forEach((station) => {
    const color = colorByTemperature(station.temperature_c);
    L.circleMarker([station.lat, station.lon], {
      radius: radiusByTemperature(station.temperature_c),
      fillColor: color,
      fillOpacity: 0.85,
      color: "#ffffff",
      weight: 1,
    })
      .bindPopup(markerPopup(station))
      .addTo(state.markerLayer);

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

function initMap() {
  state.map = L.map("map", {
    center: [23.7, 121.0],
    zoom: 7,
    preferCanvas: true,
  });

  state.baseLayers = {
    osm: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }),
    topo: L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17,
      attribution:
        'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, SRTM | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
    }),
  };

  state.activeBaseLayer = state.baseLayers.osm.addTo(state.map);
  state.markerLayer = L.layerGroup().addTo(state.map);
  state.labelLayer = L.layerGroup().addTo(state.map);
  state.map.on("zoomend", renderMarkers);
  renderMarkers();
}

function switchBaseMap() {
  if (!state.map) return;
  if (state.activeBaseLayer) {
    state.map.removeLayer(state.activeBaseLayer);
  }
  state.activeBaseLayer = state.baseLayers[baseMapSelect.value].addTo(state.map);
}

baseMapSelect.addEventListener("change", switchBaseMap);
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
