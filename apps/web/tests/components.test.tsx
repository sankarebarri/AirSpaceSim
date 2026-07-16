import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppFrame } from "../src/components/AppFrame";

const routerFuture = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

describe("AppFrame", () => {
  it("renders the shared hosted navigation shell", () => {
    render(
      <MemoryRouter future={routerFuture}>
        <AppFrame>
          <section>Dashboard body</section>
        </AppFrame>
      </MemoryRouter>,
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
