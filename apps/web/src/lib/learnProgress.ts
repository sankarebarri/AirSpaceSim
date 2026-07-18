// Guest-only progress for the Learn experience. No authenticated persistence
// exists yet, so this is deliberately local-only ("if convenient" per spec)
// rather than a real backend-backed progress system.

const STORAGE_KEY = "airspacesim.learn-progress.v1";

export interface LearnProgressEntry {
  conceptId: string;
  title: string;
  stageLabel: string;
  stage: number;
  totalStages: number;
  started: boolean;
  completed: boolean;
  updatedAt: string;
}

type ProgressStore = Record<string, LearnProgressEntry>;

function readStore(): ProgressStore {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" ? (parsed as ProgressStore) : {};
  } catch {
    return {};
  }
}

function writeStore(store: ProgressStore): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // Guest storage may be unavailable (private browsing, quota). Progress
    // simply won't persist across reloads in that case.
  }
}

export function getLearnProgress(conceptId: string): LearnProgressEntry | null {
  return readStore()[conceptId] ?? null;
}

export function saveLearnProgress(entry: Omit<LearnProgressEntry, "updatedAt">): void {
  const store = readStore();
  store[entry.conceptId] = { ...entry, updatedAt: new Date().toISOString() };
  writeStore(store);
}

// --- Lesson-level completion for curriculum concepts (guest, local-only) ---

const LESSON_STORAGE_KEY = "airspacesim.lesson-progress.v1";

type LessonProgressStore = Record<string, string[]>; // conceptId -> completed lesson ids

function readLessonStore(): LessonProgressStore {
  try {
    const raw = window.localStorage.getItem(LESSON_STORAGE_KEY);
    if (!raw) {
      return {};
    }
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object"
      ? (parsed as LessonProgressStore)
      : {};
  } catch {
    return {};
  }
}

export function getCompletedLessons(conceptId: string): string[] {
  const completed = readLessonStore()[conceptId];
  return Array.isArray(completed) ? completed : [];
}

export function markLessonComplete(conceptId: string, lessonId: string): void {
  const store = readLessonStore();
  const completed = new Set(store[conceptId] ?? []);
  completed.add(lessonId);
  store[conceptId] = [...completed];
  try {
    window.localStorage.setItem(LESSON_STORAGE_KEY, JSON.stringify(store));
  } catch {
    // Best-effort guest persistence only.
  }
}

export function getContinueLearningEntry(): LearnProgressEntry | null {
  const entries = Object.values(readStore()).filter(
    (entry) => entry.started && !entry.completed,
  );
  if (entries.length === 0) {
    return null;
  }
  return entries.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))[0];
}
