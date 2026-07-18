import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchCurriculum, type CurriculumConcept } from "../lib/content";
import { LanguageToggle, useI18n } from "../lib/i18n";
import { getContinueLearningEntry, type LearnProgressEntry } from "../lib/learnProgress";
import "./LearnPage.css";

function ConceptCard({ concept }: { concept: CurriculumConcept }) {
  const { t } = useI18n();
  if (concept.status !== "available") {
    return (
      <div className="learn-concept-card learn-concept-planned" aria-disabled="true">
        <div className="learn-concept-header">
          <span className="learn-concept-title">{t(concept.title_key)}</span>
          <span className="learn-status-chip">{t("learn.status.planned")}</span>
        </div>
        <p className="learn-concept-desc">{t(concept.description_key)}</p>
      </div>
    );
  }
  return (
    <Link to={`/learn/${concept.id}`} className="learn-concept-card">
      <div className="learn-concept-header">
        <span className="learn-concept-title">{t(concept.title_key)}</span>
        {concept.lessons ? (
          <span className="learn-status-chip learn-status-available">
            {t("learn.lessonCount", { count: concept.lessons.length })}
          </span>
        ) : null}
      </div>
      <p className="learn-concept-desc">{t(concept.description_key)}</p>
    </Link>
  );
}

export function LearnPage() {
  const { t } = useI18n();
  const [continueEntry, setContinueEntry] = useState<LearnProgressEntry | null>(null);
  const curriculumQuery = useQuery({
    queryKey: ["curriculum"],
    queryFn: fetchCurriculum,
  });

  useEffect(() => {
    setContinueEntry(getContinueLearningEntry());
  }, []);

  const families = curriculumQuery.data?.families ?? [];

  return (
    <div className="learn-page">
      <nav className="learn-nav">
        <Link to="/" className="learn-brand">
          AirSpaceSim
        </Link>
        <div className="learn-nav-actions">
          <LanguageToggle />
          <button type="button" className="learn-signin">
            {t("nav.signIn")}
          </button>
        </div>
      </nav>

      <main className="learn-main">
        <div className="learn-heading">
          <h1>{t("learn.title")}</h1>
          <p>{t("learn.subtitle")}</p>
        </div>

        {continueEntry ? (
          <section className="learn-continue">
            <div className="learn-continue-label">{t("learn.continueLearning")}</div>
            <div className="learn-continue-card">
              <div>
                <div className="learn-continue-title">{continueEntry.title}</div>
                <div className="learn-continue-stage">{continueEntry.stageLabel}</div>
              </div>
              <Link to="/lessons/crossing-traffic/learn" className="learn-continue-btn">
                {t("home.continue")}
              </Link>
            </div>
          </section>
        ) : null}

        {families.map((family) => (
          <section className="learn-concepts" key={family.id}>
            <div className="learn-concepts-label">{t(family.title_key)}</div>
            <p className="learn-family-desc">{t(family.description_key)}</p>
            <div className="learn-concepts-grid">
              {family.concepts.map((concept) => (
                <ConceptCard concept={concept} key={concept.id} />
              ))}
            </div>
          </section>
        ))}

        <section className="learn-concepts">
          <div className="learn-concepts-label">{t("learn.otherConcepts")}</div>
          <div className="learn-concepts-grid">
            <Link to="/lessons/crossing-traffic" className="learn-concept-card">
              <div className="learn-concept-header">
                <span className="learn-concept-title">
                  {t("curriculum.crossing_traffic.title")}
                </span>
              </div>
              <p className="learn-concept-desc">
                {t("curriculum.crossing_traffic.description")}
              </p>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
