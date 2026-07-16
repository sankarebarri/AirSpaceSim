import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

interface AppFrameProps {
  children: ReactNode;
  pageClassName?: string;
}

export function AppFrame({ children, pageClassName }: AppFrameProps) {
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
            Home
          </NavLink>
          <NavLink
            to="/runs"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            Simulation
          </NavLink>
          <NavLink
            to="/lessons"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            Lessons
          </NavLink>
          <NavLink
            to="/airspaces"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            Airspaces
          </NavLink>
          <NavLink
            to="/scenarios"
            className={({ isActive }) =>
              isActive ? "topnav-link topnav-link-active" : "topnav-link"
            }
          >
            Scenarios
          </NavLink>
        </nav>
      </header>

      <main className={pageClassName ? `page-shell ${pageClassName}` : "page-shell"}>
        {children}
      </main>

      <footer className="site-footer">
        <span>
          Training and visualization only — not certified for real ATC,
          aircraft operations, or navigation.
        </span>
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
