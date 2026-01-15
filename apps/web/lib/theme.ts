export type ThemeMode = "dark" | "light";

export const THEME_TOKENS = {
  radii: {
    sm: "10px",
    md: "14px",
    lg: "18px",
  },
  shadows: {
    sm: "0 6px 18px rgba(0, 0, 0, 0.25)",
    md: "0 10px 30px rgba(0, 0, 0, 0.35)",
  },
};

const STORAGE_KEY = "ads_theme_mode";

export function getStoredTheme(): ThemeMode {
  if (typeof window === "undefined") {
    return "dark";
  }
  const value = window.localStorage.getItem(STORAGE_KEY);
  return value === "light" ? "light" : "dark";
}

export function setStoredTheme(mode: ThemeMode) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, mode);
}

export function applyTheme(mode: ThemeMode) {
  if (typeof document === "undefined") {
    return;
  }
  document.documentElement.setAttribute("data-theme", mode);
}
