// Account page: guest sign-in/register flow and signed-in profile view.

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AccountPage } from "../src/pages/AccountPage";
import { LanguageProvider } from "../src/lib/i18n";
import { installJsonFetchMock } from "./http";

const API = "http://127.0.0.1:8000";

const USER = {
  id: "user-1",
  email: "trainee@example.test",
  display_name: "Trainee",
  preferred_language: "en",
  created_at: "2026-07-18T08:00:00Z",
};

function renderAccount() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <LanguageProvider>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/account"]}>
          <AccountPage />
        </MemoryRouter>
      </QueryClientProvider>
    </LanguageProvider>,
  );
}

describe("AccountPage", () => {
  it("lets a guest sign in and shows the profile with persistence note", async () => {
    installJsonFetchMock([
      {
        path: `${API}/api/v1/auth/me`,
        response: { body: { detail: "Not signed in." }, status: 401 },
      },
      { path: `${API}/api/v1/auth/login`, method: "POST", response: { body: USER } },
    ]);
    renderAccount();

    // Guest view explains what an account adds without blocking guest use.
    expect(await screen.findByText(/without an account/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "trainee@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "training-pass-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Your account")).toBeInTheDocument();
    expect(screen.getByText("trainee@example.test")).toBeInTheDocument();
    expect(screen.getByLabelText("Preferred language")).toHaveValue("en");
    expect(
      screen.getByRole("button", { name: "Sign out" }),
    ).toBeInTheDocument();
  });

  it("shows a readable error for wrong credentials", async () => {
    installJsonFetchMock([
      {
        path: `${API}/api/v1/auth/me`,
        response: { body: { detail: "Not signed in." }, status: 401 },
      },
      {
        path: `${API}/api/v1/auth/login`,
        method: "POST",
        response: { body: { detail: "Incorrect email or password." }, status: 401 },
      },
    ]);
    renderAccount();

    await screen.findByText(/without an account/);
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "trainee@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrong" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() =>
      expect(
        screen.getByText("Incorrect email or password."),
      ).toBeInTheDocument(),
    );
  });
});
