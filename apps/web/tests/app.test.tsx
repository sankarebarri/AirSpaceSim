import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../src/app/App";

describe("App", () => {
  it("renders the homepage on the overview route", () => {
    window.history.pushState({}, "", "/");
    render(<App />);

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Learn/ })).toHaveAttribute("href", "/lessons");
    expect(screen.getByRole("link", { name: /Practice/ })).toHaveAttribute("href", "/scenarios");
    expect(screen.getByRole("link", { name: /Simulate/ })).toHaveAttribute("href", "/simulate");
    // Sign in is a real link to the account page now (no dead controls).
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/account",
    );
  });
});
