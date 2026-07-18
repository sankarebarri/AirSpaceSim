import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchCurriculum, type CurriculumConcept } from "../lib/content";
import { LanguageToggle, useI18n } from "../lib/i18n";
import { getCompletedLessons } from "../lib/learnProgress";
import "./LearnPage.css";
import "./ConceptPage.css";

function findConcept(
  families: { concepts: CurriculumConcept[] }[] | undefined,
  conceptId: string | undefined,
): CurriculumConcept | null {
  if (!families || !conceptId) {
    return null;
  }
  for (const family of families) {
    const match = family.concepts.find((concept) => concept.id === conceptId);
    if (match) {
      return match;
    }
  }
  return null;
}

export function ConceptPage() {
  const { t } = useI18n();
  const { conceptId } = useParams<{ conceptId: string }>();
  const [completed, setCompleted] = useState<string[]>([]);
  const curriculumQuery = useQuery({
    queryKey: ["curriculum"],
    queryFn: fetchCurriculum,
  });
  const concept = findConcept(curriculumQuery.data?.families, conceptId);

  useEffect(() => {
    if (conceptId) {
      setCompleted(getCompletedLessons(conceptId));
    }
  }, [conceptId]);

  return (
    <div className="learn-page">
      <nav className="learn-nav">
        <Link to="/" className="learn-brand">
          AirSpaceSim
        </Link>
        <div className="learn-nav-actions">
          <LanguageToggle />
          <Link to="/lessons" className="learn-signin">
            {t("concept.backToLearn")}
          </Link>
        </div>
      </nav>

      <main className="learn-main">
        {concept ? (
          <>
            <div className="learn-heading">
              <h1>{t(concept.title_key)}</h1>
              <p>{t(concept.overview_key ?? concept.description_key)}</p>
            </div>

            {concept.status === "available" && concept.lessons ? (
              <section className="learn-concepts">
                <div className="learn-concepts-label">{t("concept.journey")}</div>
                <ol className="concept-journey">
                  {concept.lessons.map((lesson, index) => {
                    const isCompleted = completed.includes(lesson.lesson_id);
                    const firstIncomplete =
                      concept.lessons?.findIndex(
                        (entry) => !completed.includes(entry.lesson_id),
                      ) === index;
                    return (
                      <li className="concept-journey-item" key={lesson.lesson_id}>
                        <span
                          className={
                            isCompleted
                              ? "concept-step-mark concept-step-done"
                              : "concept-step-mark"
                          }
                          aria-hidden="true"
                        >
                          {isCompleted ? "✓" : index + 1}
                        </span>
                        <span className="concept-step-title">
                          {t(lesson.title_key)}
                          {isCompleted ? (
                            <span className="concept-step-status">
                              {t("concept.completed")}
                            </span>
                          ) : null}
                        </span>
                        <Link
                          to={`/learn/${concept.id}/${lesson.lesson_id}`}
                          className={
                            firstIncomplete
                              ? "concept-step-action concept-step-primary"
                              : "concept-step-action"
                          }
                        >
                          {isCompleted ? t("concept.review") : t("concept.start")}
                        </Link>
                      </li>
                    );
                  })}
                </ol>
              </section>
            ) : (
              <section className="learn-concepts">
                <p className="concept-planned-note">{t("concept.plannedNote")}</p>
                {concept.planned_outline_keys ? (
                  <ul className="concept-outline">
                    {concept.planned_outline_keys.map((key) => (
                      <li key={key}>{t(key)}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            )}

            {concept.related_next ? (
              <section className="learn-concepts">
                <div className="learn-concepts-label">{t("concept.relatedNext")}</div>
                <div className="learn-concepts-grid">
                  <Link to={concept.related_next.path} className="learn-concept-card">
                    <div className="learn-concept-header">
                      <span className="learn-concept-title">
                        {t(concept.related_next.title_key)}
                      </span>
                    </div>
                    {concept.related_next.note_key ? (
                      <p className="learn-concept-desc">
                        {t(concept.related_next.note_key)}
                      </p>
                    ) : null}
                  </Link>
                </div>
              </section>
            ) : null}
          </>
        ) : (
          <div className="learn-heading">
            <p>{curriculumQuery.isPending ? t("runner.loading") : t("runner.error")}</p>
          </div>
        )}
      </main>
    </div>
  );
}
