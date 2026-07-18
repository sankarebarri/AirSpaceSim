import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getContinueLearningEntry, type LearnProgressEntry } from "../lib/learnProgress";
import { LanguageToggle, useI18n } from "../lib/i18n";
import "./HomePage.css";

interface PrimaryAction {
  key: string;
  labelKey: string;
  descriptionKey: string;
  href: string;
}

const primaryActions: PrimaryAction[] = [
  {
    key: "learn",
    labelKey: "home.learn.title",
    descriptionKey: "home.learn.description",
    href: "/lessons",
  },
  {
    key: "practice",
    labelKey: "home.practice.title",
    descriptionKey: "home.practice.description",
    href: "/scenarios",
  },
  {
    key: "simulate",
    labelKey: "home.simulate.title",
    descriptionKey: "home.simulate.description",
    href: "/simulate",
  },
];

export function HomePage() {
  const { t } = useI18n();
  const [continueEntry, setContinueEntry] = useState<LearnProgressEntry | null>(null);

  useEffect(() => {
    setContinueEntry(getContinueLearningEntry());
  }, []);

  return (
    <div className="landing-page">
      <nav className="home-nav">
        <Link to="/" className="home-brand">
          AirSpaceSim
        </Link>
        <div className="home-nav-actions">
          <LanguageToggle />
          <Link to="/account" className="home-signin">
            {t("nav.signIn")}
          </Link>
        </div>
      </nav>

      <main className="home-main">
        <h1 className="home-tagline">
          {t("home.tagline1")}
          <br />
          {t("home.tagline2")}
        </h1>

        <div className="home-actions">
          {primaryActions.map((action) => (
            <Link to={action.href} className="home-action" key={action.key}>
              <span className="home-action-label">{t(action.labelKey)}</span>
              <p className="home-action-desc">{t(action.descriptionKey)}</p>
            </Link>
          ))}
        </div>

        {continueEntry ? (
          <div className="home-continue">
            <div className="home-continue-label">{t("home.continueTraining")}</div>
            <div className="home-continue-card">
              <div>
                <div className="home-continue-title">{continueEntry.title}</div>
                <div className="home-continue-stage">{continueEntry.stageLabel}</div>
              </div>
              <Link to="/lessons/crossing-traffic/learn" className="home-continue-btn">
                {t("home.continue")}
              </Link>
            </div>
          </div>
        ) : null}
      </main>

      <footer className="home-footer">
        <span className="home-footer-brand">AirSpaceSim</span>
        <p className="home-footer-legal">{t("footer.disclaimer")}</p>
      </footer>
    </div>
  );
}
