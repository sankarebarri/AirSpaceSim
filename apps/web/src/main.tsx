import ReactDOM from "react-dom/client";
import "leaflet/dist/leaflet.css";

import { App } from "./app/App";
import "./styles/index.css";

// Leaflet owns imperative DOM state and is more reliable here without
// React's development-only double mount behavior from StrictMode.
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(<App />);
