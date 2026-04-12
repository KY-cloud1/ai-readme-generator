import { describe, test, expect, beforeEach } from '@jest/globals';
import { getSettings, saveSettings, updateSetting } from '../src/app/api/settings/storage';

describe('Settings (localStorage)', () => {
  let mockStorage: Record<string, string>;

  beforeEach(() => {
    mockStorage = {};
    localStorage.clear();
    delete (global as any).localStorage;
    Object.defineProperty(global, 'localStorage', {
      value: {
        getItem: jest.fn((key: string) => mockStorage[key] || null),
        setItem: jest.fn((key: string, value: string) => {
          mockStorage[key] = value;
        }),
        removeItem: jest.fn((key: string) => {
          delete mockStorage[key];
        }),
        clear: jest.fn(() => {
          Object.keys(mockStorage).forEach((key) => delete mockStorage[key]);
        }),
      },
      writable: true,
    });
  });

  test('should return default settings if none exist', () => {
    const settings = getSettings();
    expect(settings.apiKey).toBe('');
    expect(settings.timeout).toBe(300);
    expect(settings.model).toBe('claude-3-5-sonnet-20240620');
    expect(settings.autoDownload).toBe(true);
  });

  test('should return saved settings', () => {
    const testSettings = {
      apiKey: 'test-key-123',
      timeout: 600,
      model: 'claude-3-opus-20240229',
      autoDownload: false,
    };
    localStorage.setItem('ai-readme-gen-settings', JSON.stringify(testSettings));

    const settings = getSettings();
    expect(settings.apiKey).toBe('test-key-123');
    expect(settings.timeout).toBe(600);
    expect(settings.model).toBe('claude-3-opus-20240229');
    expect(settings.autoDownload).toBe(false);
  });

  test('should save settings', () => {
    const newSettings = {
      apiKey: 'new-api-key',
      timeout: 450,
      model: 'claude-3-sonnet-20240229',
      autoDownload: true,
    };
    saveSettings(newSettings);

    const saved = getSettings();
    expect(saved.apiKey).toBe('new-api-key');
    expect(saved.timeout).toBe(450);
    expect(saved.model).toBe('claude-3-sonnet-20240229');
    expect(saved.autoDownload).toBe(true);
  });

  test('should update single setting', () => {
    const initialSettings = {
      apiKey: 'initial-key',
      timeout: 300,
      model: 'claude-3-5-sonnet-20240620',
      autoDownload: true,
    };
    localStorage.setItem('ai-readme-gen-settings', JSON.stringify(initialSettings));

    updateSetting('timeout', 500);

    const updated = getSettings();
    expect(updated.timeout).toBe(500);
    expect(updated.apiKey).toBe('initial-key');
  });

  test('should persist data across sessions', () => {
    const testSettings = {
      apiKey: 'persistent-key',
      timeout: 400,
      model: 'claude-3-haiku-20240307',
      autoDownload: false,
    };
    localStorage.setItem('ai-readme-gen-settings', JSON.stringify(testSettings));

    // Simulate new session
    localStorage.clear();
    localStorage.setItem('ai-readme-gen-settings', JSON.stringify(testSettings));

    const settings = getSettings();
    expect(settings.apiKey).toBe('persistent-key');
    expect(settings.timeout).toBe(400);
  });

  test('should handle invalid JSON gracefully', () => {
    localStorage.setItem('ai-readme-gen-settings', 'invalid json');

    const settings = getSettings();
    // Should return defaults
    expect(settings.apiKey).toBe('');
    expect(settings.timeout).toBe(300);
  });
});
