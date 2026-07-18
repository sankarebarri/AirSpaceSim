// Account page: guest sign-in/registration and signed-in profile.
// Authentication adds persistence (progress, run history, language
// preference) — guests keep full Learn/Practice/solo-Simulate access.

import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchCurrentUser,
  login,
  logout,
  register,
  updateProfile,
} from "../lib/auth";
import { LanguageToggle, useI18n, type Language } from "../lib/i18n";
import "./LearnPage.css";
import "./AccountPage.css";

export function AccountPage() {
  const { t, setLanguage } = useI18n();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [profileNotice, setProfileNotice] = useState<string | null>(null);

  const userQuery = useQuery({
    queryKey: ["current-user"],
    queryFn: fetchCurrentUser,
  });
  const user = userQuery.data ?? null;

  const applyUserLanguage = (language: string) => {
    if (language === "en" || language === "fr") {
      setLanguage(language as Language);
    }
  };

  const authMutation = useMutation({
    mutationFn: async () => {
      if (mode === "register") {
        return register({
          email,
          password,
          display_name: displayName || undefined,
        });
      }
      return login({ email, password });
    },
    onSuccess: (signedIn) => {
      setFormError(null);
      setPassword("");
      applyUserLanguage(signedIn.preferred_language);
      queryClient.setQueryData(["current-user"], signedIn);
    },
    onError: (error: unknown) => {
      setFormError(error instanceof Error ? error.message : String(error));
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(["current-user"], null);
      setProfileNotice(null);
    },
  });

  const profileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: (updated) => {
      queryClient.setQueryData(["current-user"], updated);
      applyUserLanguage(updated.preferred_language);
      setProfileNotice(t("account.saved"));
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    authMutation.mutate();
  };

  return (
    <div className="learn-page">
      <nav className="learn-nav">
        <Link to="/" className="learn-brand">
          AirSpaceSim
        </Link>
        <div className="learn-nav-actions">
          <LanguageToggle />
          <Link to="/lessons" className="learn-signin">
            {t("nav.lessons")}
          </Link>
        </div>
      </nav>

      <main className="learn-main account-main">
        {user ? (
          <section className="account-card">
            <h1>{t("account.title")}</h1>
            <p className="account-email">{user.email}</p>
            {profileNotice ? (
              <p className="account-notice">{profileNotice}</p>
            ) : null}

            <label className="account-field">
              <span>{t("account.displayName")}</span>
              <input
                defaultValue={user.display_name ?? ""}
                onBlur={(event) => {
                  const value = event.target.value.trim();
                  if (value !== (user.display_name ?? "")) {
                    profileMutation.mutate({ display_name: value || null });
                  }
                }}
              />
            </label>

            <label className="account-field">
              <span>{t("account.language")}</span>
              <select
                value={user.preferred_language}
                onChange={(event) =>
                  profileMutation.mutate({
                    preferred_language: event.target.value,
                  })
                }
              >
                <option value="en">English</option>
                <option value="fr">Français</option>
              </select>
            </label>

            <p className="account-hint">{t("account.persistenceNote")}</p>

            <button
              type="button"
              className="account-secondary"
              onClick={() => logoutMutation.mutate()}
            >
              {t("account.signOut")}
            </button>
          </section>
        ) : (
          <section className="account-card">
            <h1>
              {mode === "login" ? t("account.signIn") : t("account.register")}
            </h1>
            <p className="account-hint">{t("account.guestNote")}</p>

            <form onSubmit={submit} className="account-form">
              <label className="account-field">
                <span>{t("account.email")}</span>
                <input
                  type="email"
                  required
                  value={email}
                  autoComplete="email"
                  onChange={(event) => setEmail(event.target.value)}
                />
              </label>
              <label className="account-field">
                <span>{t("account.password")}</span>
                <input
                  type="password"
                  required
                  minLength={mode === "register" ? 8 : 1}
                  value={password}
                  autoComplete={
                    mode === "register" ? "new-password" : "current-password"
                  }
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              {mode === "register" ? (
                <label className="account-field">
                  <span>{t("account.displayNameOptional")}</span>
                  <input
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                  />
                </label>
              ) : null}

              {formError ? <p className="account-error">{formError}</p> : null}

              <button
                type="submit"
                className="account-primary"
                disabled={authMutation.isPending}
              >
                {mode === "login" ? t("account.signIn") : t("account.createAccount")}
              </button>
            </form>

            <button
              type="button"
              className="account-switch"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setFormError(null);
              }}
            >
              {mode === "login"
                ? t("account.switchToRegister")
                : t("account.switchToLogin")}
            </button>
          </section>
        )}
      </main>
    </div>
  );
}
