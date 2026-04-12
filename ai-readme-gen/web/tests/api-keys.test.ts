import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

describe('API Keys', () => {
  let userId: string;

  beforeAll(async () => {
    // Create a test user
    const user = await prisma.user.create({
      data: {
        email: 'apikey-test@example.com',
        password: 'Test123456',
        name: 'API Key Test User',
      },
    });
    userId = user.id;
  });

  afterAll(async () => {
    // Clean up test data
    await prisma.apikey.deleteMany({
      where: { userId },
    });

    await prisma.user.deleteMany({
      where: { email: 'apikey-test@example.com' },
    });

    await prisma.$disconnect();
  });

  test('should generate API key', async () => {
    const apiKey = `ak_${Math.random().toString(36).substring(2, 36)}`;

    const created = await prisma.apikey.create({
      data: {
        userId,
        name: 'Test API Key',
        key: apiKey,
        prefix: 'ak_',
        permissions: ['projects:read', 'projects:write', 'settings:read', 'settings:write'],
        isActive: true,
      },
    });

    expect(created.id).toBeDefined();
    expect(created.name).toBe('Test API Key');
    expect(created.key).toBe(apiKey);
    expect(created.isActive).toBe(true);
    expect(created.permissions).toContain('projects:read');
  });

  test('should list active API keys', async () => {
    await prisma.apikey.create({
      data: {
        userId,
        name: 'Active Key 1',
        key: `ak_${Math.random().toString(36).substring(2, 36)}`,
        isActive: true,
      },
    });

    await prisma.apikey.create({
      data: {
        userId,
        name: 'Active Key 2',
        key: `ak_${Math.random().toString(36).substring(2, 36)}`,
        isActive: true,
      },
    });

    const apikeys = await prisma.apikey.findMany({
      where: {
        userId,
        isActive: true,
      },
    });

    expect(apikeys.length).toBe(2);
    apikeys.forEach((ak) => expect(ak.userId).toBe(userId));
  });

  test('should deactivate API key', async () => {
    const apiKey = `ak_${Math.random().toString(36).substring(2, 36)}`;

    await prisma.apikey.create({
      data: {
        userId,
        name: 'To Be Deactivated',
        key: apiKey,
        isActive: true,
      },
    });

    const deactivated = await prisma.apikey.update({
      where: {
        id: { startsWith: 'apikey_' }, // This will need to be updated with actual ID
        userId,
      },
      data: {
        isActive: false,
      },
    });

    expect(deactivated.isActive).toBe(false);
  });

  test('should not list inactive API keys', async () => {
    const activeKey = `ak_${Math.random().toString(36).substring(2, 36)}`;

    await prisma.apikey.create({
      data: {
        userId,
        name: 'Active Key',
        key: activeKey,
        isActive: true,
      },
    });

    const inactiveKey = `ak_${Math.random().toString(36).substring(2, 36)}`;

    await prisma.apikey.create({
      data: {
        userId,
        name: 'Inactive Key',
        key: inactiveKey,
        isActive: false,
      },
    });

    const activeKeys = await prisma.apikey.findMany({
      where: {
        userId,
        isActive: true,
      },
    });

    const inactiveKeys = await prisma.apikey.findMany({
      where: {
        userId,
        isActive: false,
      },
    });

    expect(activeKeys.length).toBe(1);
    expect(inactiveKeys.length).toBe(1);
  });
});
