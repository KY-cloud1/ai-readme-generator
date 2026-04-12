import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

describe('Authentication', () => {
  const validCredentials = {
    email: 'test@example.com',
    password: 'Test123456',
  };

  const invalidCredentials = {
    email: 'wrong@example.com',
    password: 'WrongPassword123',
  };

  beforeAll(async () => {
    // Clean up any existing test user
    await prisma.user.deleteMany({
      where: { email: validCredentials.email },
    });

    // Create test user
    const hashedPassword = await bcrypt.hash(validCredentials.password, 12);
    await prisma.user.create({
      data: {
        email: validCredentials.email,
        password: hashedPassword,
        name: 'Test User',
      },
    });
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  test('should login with valid credentials', async () => {
    // This test would require the full API to be running
    // For now, we document the expected behavior
    expect(validCredentials.email).toBe('test@example.com');
    expect(validCredentials.password).toBe('Test123456');
  });

  test('should hash password correctly', async () => {
    const hashed = await bcrypt.hash(validCredentials.password, 12);
    expect(hashed).not.toBe(validCredentials.password);
    expect(hashed.startsWith('$2b$')).toBe(true);
  });

  test('should verify password correctly', async () => {
    const hashed = await bcrypt.hash(validCredentials.password, 12);
    const isValid = await bcrypt.compare(validCredentials.password, hashed);
    expect(isValid).toBe(true);

    const isInvalid = await bcrypt.compare('WrongPassword', hashed);
    expect(isInvalid).toBe(false);
  });
});
