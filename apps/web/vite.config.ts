import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const baseConfig = {
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5174
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    clearMocks: true
  }
};

export default defineConfig(({ mode }) => {
  if (mode === "production" && !process.env.VITE_API_BASE_URL) {
    // Loud build-time warning: a production bundle without an API base URL
    // silently falls back to localhost and cannot work when hosted.
    console.warn(
      "\n[airspacesim] WARNING: building for production without " +
        "VITE_API_BASE_URL — the bundle will target http://127.0.0.1:8000.\n",
    );
  }
  return baseConfig;
});
