"use client";

import { useState, useEffect } from "react";

interface SettingsState {
  apiKey: string;
  timeout: number;
  model: string;
  autoDownload: boolean;
}

const defaultSettings: SettingsState = {
  apiKey: "",
  timeout: 300,
  model: "claude-3-5-sonnet-20240620",
  autoDownload: true,
};

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [timeout, setTimeoutValue] = useState(300);
  const [model, setModel] = useState(defaultSettings.model);
  const [autoDownload, setAutoDownload] = useState(true);

  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("settings");
    if (saved) {
      try {
        const parsed: SettingsState = JSON.parse(saved);
        setApiKey(parsed.apiKey || "");
        setTimeoutValue(parsed.timeout || 300);
        setModel(parsed.model || defaultSettings.model);
        setAutoDownload(parsed.autoDownload !== false);
      } catch {
        console.error("Failed to parse saved settings");
      }
    }
  }, []);

  useEffect(() => {
    if (saveSuccess) {
      const timer = setTimeout(() => setSaveSuccess(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [saveSuccess]);

  const handleSave = () => {
    const settings: SettingsState = {
      apiKey,
      timeout,
      model,
      autoDownload,
    };

    localStorage.setItem("settings", JSON.stringify(settings));
    setSaveSuccess(true);
  };

  const handleReset = () => {
    setApiKey("");
    setTimeoutValue(300);
    setModel(defaultSettings.model);
    setAutoDownload(true);
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <div className="max-w-3xl mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8">Settings</h1>

        <div className="space-y-6">
          {/* API Key */}
          <section className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold mb-4">API Configuration</h2>

            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter API key"
              className="w-full px-3 py-2 border rounded-lg"
            />
          </section>

          {/* Model */}
          <section className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold mb-4">AI Model</h2>

            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet</option>
              <option value="claude-3-opus-20240229">Claude 3 Opus</option>
              <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
              <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
            </select>
          </section>

          {/* Timeout */}
          <section className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold mb-4">Analysis Settings</h2>

            <input
              type="number"
              value={timeout}
              onChange={(e) => setTimeoutValue(Number(e.target.value))}
              min={30}
              max={600}
              className="w-full px-3 py-2 border rounded-lg"
            />

            <label className="flex items-center mt-4">
              <input
                type="checkbox"
                checked={autoDownload}
                onChange={(e) => setAutoDownload(e.target.checked)}
              />
              <span className="ml-2">Auto download README</span>
            </label>
          </section>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={handleSave}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg"
            >
              Save Settings
            </button>

            <button
              onClick={handleReset}
              className="px-6 py-2 bg-gray-300 rounded-lg"
            >
              Reset
            </button>
          </div>

          {saveSuccess && (
            <p className="text-green-600 text-sm">Settings saved locally</p>
          )}
        </div>
      </div>
    </main>
  );
}