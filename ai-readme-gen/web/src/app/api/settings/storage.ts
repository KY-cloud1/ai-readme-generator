/**
 * LocalStorage-based settings storage for ai-readme-gen
 * No authentication required - all data stored locally in browser
 */

interface Settings {
  apiKey: string;
  timeout: number;
  model: string;
  autoDownload: boolean;
}

const STORAGE_KEY = "ai-readme-gen-settings";

const defaultSettings: Settings = {
  apiKey: "",
  timeout: 300,
  model: "claude-3-5-sonnet-20240620",
  autoDownload: true,
};

/**
 * Get settings (returns default if none exist)
 */
export function getSettings(): Settings {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) {
      return defaultSettings;
    }
    return JSON.parse(data);
  } catch {
    return defaultSettings;
  }
}

/**
 * Save full settings object
 */
export function saveSettings(data: Partial<Settings>): void {
  const current = getSettings();
  const updated = {
    ...current,
    ...data,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

/**
 * Update single setting field
 */
export function updateSetting<K extends keyof Settings>(
  key: K,
  value: Settings[K]
): void {
  const settings = getSettings();
  settings[key] = value;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}
