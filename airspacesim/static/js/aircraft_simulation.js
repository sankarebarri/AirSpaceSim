// aricraft_simulation.py
import { map } from "./map_renderer.js";
const AIRCRAFT_CONFIG_URL = "aircraft_data.json";
let markers = {}; // Dictionary to track markers

async function fetchAircraftData() {
  try {
    const response = await fetch(AIRCRAFT_CONFIG_URL);
    const data = await response.json();
    console.log("Fetched aircraft data:", data);
    updateMarkers(data.aircraft_data);
  } catch (error) {
    console.error("Error fetching aircraft data:", error);
  }
}

function updateMarkers(aircraftData) {
  aircraftData.forEach((aircraft) => {
    const markerId = aircraft.id;
    const coords = aircraft.position;
    const callsign = aircraft.callsign;
    const speed = aircraft.speed;

    if (markers[markerId]) {
      console.log(`Updating marker ${markerId} to ${coords}`);
      markers[markerId].setLatLng(coords);
      markers[markerId].setTooltipContent(
        `Callsign: ${callsign}, Speed: ${speed} knots`
      );
    } else {
      console.log(`Adding new marker for ${markerId}`);
      const marker = L.marker(coords, {
        icon: L.icon({
          iconUrl: "static/icons/circle.svg",
          iconSize: [10, 10],
        }),
      }).bindTooltip(`Callsign: ${callsign}, Speed: ${speed} knots`, {
        permanent: true,
        direction: "bottom",
      });

      marker.addTo(map);
      markers[markerId] = marker;
    }
  });
}

setInterval(fetchAircraftData, 200);
