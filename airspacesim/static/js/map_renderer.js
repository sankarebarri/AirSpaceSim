// // static/js/map_renderer.js
const CONFIG_URL = "gao_airspace_config.json";
export let map; // Export map instance for use in other scripts

async function loadMapConfig() {
  try {
    const response = await fetch(CONFIG_URL);
    const config = await response.json();
    initializeMap(config);
  } catch (error) {
    console.error("Error loading map configuration:", error);
  }
}

function initializeMap(config) {
  map = L.map("map").setView(config.center, config.zoom);
  console.log("Map initialized:", map);
  if (config.tile_layer) {
    L.tileLayer(config.tile_layer.url, {
      attribution: config.tile_layer.attribution,
      maxZoom: 19,
    }).addTo(map);
  }

  config.elements.forEach((element) => {
    if (element.type === "circle") {
      L.circle(element.center, {
        radius: element.radius,
        color: element.color || "blue",
        fillColor: element.fill_color || "blue",
        fillOpacity: element.fill_opacity || 0.2,
      })
        .addTo(map)
        .bindPopup(element.name || "");
    } else if (element.type === "polyline") {
      L.polyline(element.coords, {
        color: element.color || "green",
        weight: element.weight || 3,
        opacity: element.opacity || 1,
      })
        .addTo(map)
        .bindPopup(element.name || "");
    } else if (element.type === "marker") {
      const marker = L.marker(element.coords, {
        icon: L.icon({
          iconUrl: element.icon_url || "static/icons/triangle_9.svg",
          iconSize: element.icon_size || [20, 20],
        }),
      })
        .addTo(map)
        .bindPopup(element.popup_text || "");

      if (element.label_text) {
        marker.bindTooltip(element.label_text, {
          permanent: true,
          direction: "top",
        });
      }
    }
  });
}

loadMapConfig();
