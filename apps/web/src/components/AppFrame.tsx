import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { LanguageToggle, useI18n } from "../lib/i18n";

interface AppFrameProps {
  children: ReactNode;
  pageClassName?: string;
}

export function AppFrame({ children, pageClassName }: AppFrameProps) {
  const { t } = useI18n();
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <NavLink to="/" className="brand-mark">
            AirSpaceSim
          </NavLink>
          <p className="brand-note">ATC training simulator</p>
        </div>

        <nav className="topnav" aria-label="Primary">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            {t("nav.home")}
          </NavLink>
          <NavLink
            to="/runs"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            {t("nav.simulation")}
          </NavLink>
          <NavLink
            to="/lessons"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            {t("nav.lessons")}
          </NavLink>
          <NavLink
            to="/airspaces"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            {t("nav.airspaces")}
          </NavLink>
          <NavLink
            to="/scenarios"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            {t("nav.scenarios")}
          </NavLink>
          <NavLink
            to="/account"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            {t("nav.account")}
          </NavLink>
        </nav>
        <LanguageToggle className="topbar-lang" />
      </header>

      <main className={pageClassName ? `page-shell ${pageClassName}` : "page-shell"}>
        {children}
      </main>

      <footer className="site-footer">
        <span>{t("footer.disclaimer")}</span>
        <a
          href="https://github.com/sankarebarri/AirSpaceSim"
          target="_blank"
          rel="noreferrer"
        >
          View on GitHub
        </a>
      </footer>
    </div>
  );
}
