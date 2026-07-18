import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppFrame } from "../src/components/AppFrame";
import { LanguageProvider } from "../src/lib/i18n";

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

describe("AppFrame", () => {
  it("renders the shared hosted navigation shell", () => {
    render(
      <LanguageProvider>
        <MemoryRouter future={routerFuture}>
          <AppFrame>
            <section>Dashboard body</section>
          </AppFrame>
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole("link", { name: "AirSpaceSim" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Simulation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Lessons" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Airspaces" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Scenarios" })).toBeInTheDocument();
    expect(screen.getByText("Dashboard body")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "View on GitHub" }),
    ).toBeInTheDocument();
  });
});
