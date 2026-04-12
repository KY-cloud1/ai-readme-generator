import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export interface Settings {
  id: string;
  userId: string;
  apiKey: string;
  timeout: number;
  model: string;
  autoDownload: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Get settings for a user
 */
export async function getSettings(userId: string): Promise<Settings> {
  const settings = await prisma.settings.findUnique({
    where: { userId },
  });

  if (!settings) {
    // Create default settings if they don't exist
    return await prisma.settings.create({
      data: {
        userId,
        apiKey: '',
        timeout: 300,
        model: 'claude-3-5-sonnet-20240620',
        autoDownload: true,
      },
    });
  }

  return settings;
}

/**
 * Save settings for a user
 */
export async function saveSettings(userId: string, settings: Partial<Settings>): Promise<Settings> {
  return prisma.settings.upsert({
    where: { userId },
    update: settings,
    create: {
      userId,
      apiKey: settings.apiKey || '',
      timeout: settings.timeout ?? 300,
      model: settings.model || 'claude-3-5-sonnet-20240620',
      autoDownload: settings.autoDownload ?? true,
    },
  });
}

/**
 * Update a specific setting for a user
 */
export async function updateSetting<K extends keyof Settings>(
  userId: string,
  key: K,
  value: Settings[K]
): Promise<void> {
  await prisma.settings.update({
    where: { userId },
    data: { [key]: value },
  });
}
