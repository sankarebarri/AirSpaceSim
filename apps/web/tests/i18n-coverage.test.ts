// Every translation key referenced by curriculum/lesson content must exist
// in BOTH locale catalogues, and the catalogues must stay in sync — so a
// missing French translation fails CI instead of silently falling back.

import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import en from "../src/locales/en.json";
import fr from "../src/locales/fr.json";

const REPO_ROOT = join(__dirname, "..", "..", "..");
const LESSONS_DIR = join(REPO_ROOT, "airspaces", "training_alpha", "lessons");

function readJson(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf-8"));
}

function collectContentKeys(value: unknown, keys: Set<string>): void {
  if (Array.isArray(value)) {
    for (const item of value) {
      collectContentKeys(item, keys);
    }
    return;
  }
  if (!value || typeof value !== "object") {
    return;
  }
  for (const [field, fieldValue] of Object.entries(value)) {
    if (field.endsWith("_key") && typeof fieldValue === "string") {
      keys.add(fieldValue);
    } else if (field.endsWith("_keys") && Array.isArray(fieldValue)) {
      for (const key of fieldValue) {
        if (typeof key === "string") {
          keys.add(key);
        }
      }
    } else if (field === "options" && Array.isArray(fieldValue)) {
      for (const option of fieldValue) {
        if (typeof option === "string") {
          keys.add(`lessons.classify.options.${option}`);
        }
      }
    } else {
      collectContentKeys(fieldValue, keys);
    }
  }
}

describe("i18n content coverage", () => {
  const referencedKeys = new Set<string>();
  collectContentKeys(readJson(join(REPO_ROOT, "content", "curriculum.v1.json")), referencedKeys);
  for (const file of readdirSync(LESSONS_DIR)) {
    if (file.startsWith("tr_") && file.endsWith(".json")) {
      collectContentKeys(readJson(join(LESSONS_DIR, file)), referencedKeys);
    }
  }

  it("collects a meaningful number of content keys", () => {
    expect(referencedKeys.size).toBeGreaterThan(40);
  });

  it("resolves every referenced key in English", () => {
    const missing = [...referencedKeys].filter((key) => !(key in en));
    expect(missing).toEqual([]);
  });

  it("resolves every referenced key in French", () => {
    const missing = [...referencedKeys].filter((key) => !(key in fr));
    expect(missing).toEqual([]);
  });

  it("keeps the English and French catalogues key-identical", () => {
    const enKeys = Object.keys(en).sort();
    const frKeys = Object.keys(fr).sort();
    expect(frKeys).toEqual(enKeys);
  });
});
