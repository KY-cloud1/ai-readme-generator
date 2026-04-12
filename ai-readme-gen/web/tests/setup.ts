import { BeforeAll } from '@jest/globals';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

beforeAll(async () => {
  // Database connection is established by Prisma
  console.log('Test setup initialized');
});

afterAll(async () => {
  await prisma.$disconnect();
});
