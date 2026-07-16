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

export function getContinueLearningEntry(): LearnProgressEntry | null {
  const entries = Object.values(readStore()).filter(
    (entry) => entry.started && !entry.completed,
  );
  if (entries.length === 0) {
    return null;
  }
  return entries.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))[0];
}
