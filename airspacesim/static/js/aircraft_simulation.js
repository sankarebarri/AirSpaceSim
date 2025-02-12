// aricraft_simulation.py
import { map } from "./map_renderer.js"; // Use the map instance
const AIRCRAFT_CONFIG_URL = "aircraft_data.json";
let markers = {}; // Dictionary to track markers

async function fetchAircraftData() {
  try {
    const response = await fetch(AIRCRAFT_CONFIG_URL);
    const data = await response.json();
    console.log("Fetched aircraft data:", data); // Debug log
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

    // Check if the marker already exists
    if (markers[markerId]) {
      console.log(`Updating marker ${markerId} to ${coords}`); // Debug log
      // Update marker position smoothly
      markers[markerId].setLatLng(coords);
    } else {
      console.log(`Adding new marker for ${markerId}`); // Debug log
      // Add a new marker if it doesn't exist
      const marker = L.marker(coords, {
        icon: L.icon({
          iconUrl: "static/icons/circle.svg",
          iconSize: [10, 10],
        }),
      }).bindTooltip(`Callsign: ${callsign}`, {
        permanent: true,
        direction: "bottom",
      });

      marker.addTo(map);
      markers[markerId] = marker; // Save reference for future updates
    }
  });
}

// Fetch and update markers periodically
setInterval(fetchAircraftData, 200);
