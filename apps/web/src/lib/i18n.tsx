// Central internationalisation layer (EN/FR) with stable keys.
//
// Deliberately dependency-free: a ~70-line provider is enough for a
// two-language catalogue of flat keys, keeps the bundle small, and keeps
// translation resources as plain JSON under src/locales/. Operational
// simulation commands and the run workspace stay English by design
// (brief: operational interface is English-only) — those surfaces simply
// don't call t().

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import en from "../locales/en.json";
import fr from "../locales/fr.json";

export type Language = "en" | "fr";

const CATALOGUES: Record<Language, Record<string, string>> = {
  en: en as Record<string, string>,
  fr: fr as Record<string, string>,
};

const STORAGE_KEY = "airspacesim.language";

export function readStoredLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "fr") {
      return stored;
    }
    if (window.navigator.language?.toLowerCase().startsWith("fr")) {
      return "fr";
    }
  } catch {
    // Storage unavailable: fall through to English.
  }
  return "en";
}

interface I18nContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(readStoredLanguage);

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Guest preference is best-effort only.
    }
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      // Fallback chain: selected language -> English -> the key itself,
      // so a missing translation is visible but never breaks the page.
      const template = CATALOGUES[language][key] ?? CATALOGUES.en[key] ?? key;
      if (!vars) {
        return template;
      }
      return template.replace(/\{(\w+)\}/g, (match, name) =>
        name in vars ? String(vars[name]) : match,
      );
    },
    [language],
  );

  const value = useMemo(
    () => ({ language, setLanguage, t }),
    [language, setLanguage, t],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (context === null) {
    throw new Error("useI18n must be used inside a LanguageProvider");
  }
  return context;
}

export function LanguageToggle({ className }: { className?: string }) {
  const { language, setLanguage } = useI18n();
  return (
    <div
      className={className ? `lang-toggle ${className}` : "lang-toggle"}
      role="group"
      aria-label="Language"
    >
      {(["en", "fr"] as const).map((option) => (
        <button
          key={option}
          type="button"
          className={
            language === option ? "lang-option lang-option-active" : "lang-option"
          }
          aria-pressed={language === option}
          onClick={() => setLanguage(option)}
        >
          {option.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
