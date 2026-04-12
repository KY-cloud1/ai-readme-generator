"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

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

export default function SettingsPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [timeout, setTimeout] = useState(300);
  const [model, setModel] = useState("claude-3-5-sonnet-20240620");
  const [autoDownload, setAutoDownload] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = () => {
    const settings: SettingsState = { apiKey, timeout, model, autoDownload };
    localStorage.setItem("settings", JSON.stringify(settings));
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleReset = () => {
    localStorage.removeItem("settings");
    setApiKey("");
    setTimeout(300);
    setModel("claude-3-5-sonnet-20240620");
    setAutoDownload(true);
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <div className="max-w-3xl mx-auto p-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Settings</h1>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
          >
            Back
          </button>
        </div>

        <div className="space-y-6">
          {/* API Configuration */}
          <section className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold mb-4">API Configuration</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="api-key" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  id="api-key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Your API key is stored locally in your browser.
                </p>
              </div>
            </div>
          </section>

          {/* AI Model Settings */}
          <section className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold mb-4">AI Model</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="model" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Model
                </label>
                <select
                  id="model"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet</option>
                  <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                  <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                  <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                </select>
              </div>
            </div>
          </section>

          {/* Analysis Settings */}
          <section className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold mb-4">Analysis Settings</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="timeout" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Request Timeout (seconds)
                </label>
                <input
                  type="number"
                  id="timeout"
                  value={timeout}
                  onChange={(e) => setTimeout(Number(e.target.value))}
                  min={30}
                  max={600}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Maximum time to wait for AI response before timing out.
                </p>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto-download"
                  checked={autoDownload}
                  onChange={(e) => setAutoDownload(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="auto-download" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Automatically download generated README files
                </label>
              </div>
            </div>
          </section>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Settings"}
            </button>
            <button
              onClick={handleReset}
              className="px-6 py-2 bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
            >
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
