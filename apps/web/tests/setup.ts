import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import { queryClient } from "../src/app/query-client";

afterEach(() => {
  vi.useRealTimers();
  cleanup();
  queryClient.clear();
  window.localStorage.clear();
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});
