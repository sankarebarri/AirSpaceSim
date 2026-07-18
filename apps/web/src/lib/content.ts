// Client for the learning-content API: curriculum + lesson definitions.
// Lesson content is data (translation keys + scenario references), so adding
// a lesson requires JSON + locale entries only — no new pages here.

import { getSessionId } from "./session";
import { API_BASE_URL } from "./api";

export interface CurriculumLessonRef {
  lesson_id: string;
  title_key: string;
}

export interface CurriculumConcept {
  id: string;
  status: "available" | "planned";
  title_key: string;
  description_key: string;
  overview_key?: string;
  airspace_id?: string;
  lessons?: CurriculumLessonRef[];
  planned_outline_keys?: string[];
  related_next?: {
    title_key: string;
    note_key?: string;
    path: string;
  };
}

export interface CurriculumFamily {
  id: string;
  title_key: string;
  description_key: string;
  service: string;
  concepts: CurriculumConcept[];
}

export interface CurriculumResponse {
  families: CurriculumFamily[];
}

export type LessonStepType = "observe" | "classify" | "complete";

export interface LessonStep {
  type: LessonStepType;
  id: string;
  text_key?: string;
  title_key?: string;
  question_key?: string;
  explanation_key?: string;
  options?: string[];
  correct?: string;
  scenario_id?: string;
  scenario_template?: string;
  sim?: "running" | "paused";
  highlight?: string;
  point_keys?: string[];
  next_lesson_id?: string;
}

export interface LessonDefinition {
  id: string;
  title: string;
  title_key: string;
  duration_minutes: number;
  concept: string;
  lesson_steps: LessonStep[];
}

export interface LessonResponse {
  airspace_id: string;
  lesson_id: string;
  lesson: LessonDefinition;
}

async function requestContent<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      "X-Airspacesim-Session": getSessionId(),
    },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as TResponse;
}

export function fetchCurriculum(): Promise<CurriculumResponse> {
  return requestContent<CurriculumResponse>("/api/v1/content/curriculum");
}

export function fetchLesson(
  airspaceId: string,
  lessonId: string,
): Promise<LessonResponse> {
  return requestContent<LessonResponse>(
    `/api/v1/content/lessons/${airspaceId}/${lessonId}`,
  );
}
