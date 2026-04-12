import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

describe('Settings', () => {
  let userId: string;
  const defaultSettings = {
    apiKey: '',
    timeout: 300,
    model: 'claude-3-5-sonnet-20240620',
    autoDownload: true,
  };

  beforeAll(async () => {
    // Create a test user
    const user = await prisma.user.create({
      data: {
        email: 'settings-test@example.com',
        password: 'Test123456',
        name: 'Settings Test User',
      },
    });
    userId = user.id;
  });

  afterAll(async () => {
    // Clean up test data
    await prisma.settings.deleteMany({
      where: { userId },
    });

    await prisma.user.deleteMany({
      where: { email: 'settings-test@example.com' },
    });

    await prisma.$disconnect();
  });

  test('should create default settings for new user', async () => {
    const settings = await prisma.settings.findUnique({
      where: { userId },
    });

    expect(settings).toBeDefined();
    expect(settings?.apiKey).toBe(defaultSettings.apiKey);
    expect(settings?.timeout).toBe(defaultSettings.timeout);
    expect(settings?.model).toBe(defaultSettings.model);
    expect(settings?.autoDownload).toBe(defaultSettings.autoDownload);
  });

  test('should update settings', async () => {
    const newSettings = {
      apiKey: 'test-api-key-123',
      timeout: 600,
      model: 'claude-3-opus-20240229',
      autoDownload: false,
    };

    const updated = await prisma.settings.upsert({
      where: { userId },
      update: newSettings,
      create: {
        userId,
        apiKey: newSettings.apiKey,
        timeout: newSettings.timeout,
        model: newSettings.model,
        autoDownload: newSettings.autoDownload,
      },
    });

    expect(updated.apiKey).toBe(newSettings.apiKey);
    expect(updated.timeout).toBe(newSettings.timeout);
    expect(updated.model).toBe(newSettings.model);
    expect(updated.autoDownload).toBe(newSettings.autoDownload);
  });

  test('should update individual settings', async () => {
    await prisma.settings.upsert({
      where: { userId },
      update: { apiKey: 'initial-key' },
      create: {
        userId,
        apiKey: 'initial-key',
        timeout: 300,
        model: 'claude-3-5-sonnet-20240620',
        autoDownload: true,
      },
    });

    await prisma.settings.update({
      where: { userId },
      data: { timeout: 450 },
    });

    const settings = await prisma.settings.findUnique({
      where: { userId },
    });

    expect(settings?.timeout).toBe(450);
    expect(settings?.apiKey).toBe('initial-key');
  });

  test('should have unique settings per user', async () => {
    const user2 = await prisma.user.create({
      data: {
        email: 'settings-test-2@example.com',
        password: 'Test123456',
        name: 'Settings Test User 2',
      },
    });

    const settings1 = await prisma.settings.findUnique({
      where: { userId },
    });

    const settings2 = await prisma.settings.findUnique({
      where: { userId: user2.id },
    });

    expect(settings1).toBeDefined();
    expect(settings2).toBeDefined();
    expect(settings1?.userId).not.toBe(settings2?.userId);
  });
});
