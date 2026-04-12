import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

describe('Projects', () => {
  let userId: string;

  beforeAll(async () => {
    // Create a test user
    const user = await prisma.user.create({
      data: {
        email: 'project-test@example.com',
        password: 'Test123456',
        name: 'Project Test User',
      },
    });
    userId = user.id;
  });

  afterAll(async () => {
    // Clean up test data
    await prisma.project.deleteMany({
      where: { userId },
    });

    await prisma.user.deleteMany({
      where: { email: 'project-test@example.com' },
    });

    await prisma.$disconnect();
  });

  test('should create a project', async () => {
    const project = await prisma.project.create({
      data: {
        userId,
        name: 'Test Project',
        path: '/test/path',
        status: 'pending',
      },
    });

    expect(project.id).toBeDefined();
    expect(project.name).toBe('Test Project');
    expect(project.path).toBe('/test/path');
    expect(project.status).toBe('pending');
    expect(project.userId).toBe(userId);
  });

  test('should get project by ID', async () => {
    const project = await prisma.project.create({
      data: {
        userId,
        name: 'Get Test Project',
        path: '/get/path',
      },
    });

    const foundProject = await prisma.project.findUnique({
      where: { id: project.id, userId },
    });

    expect(foundProject).toBeDefined();
    expect(foundProject?.name).toBe('Get Test Project');
  });

  test('should get all projects for user', async () => {
    await prisma.project.create({
      data: {
        userId,
        name: 'Project 1',
        path: '/path1',
      },
    });

    await prisma.project.create({
      data: {
        userId,
        name: 'Project 2',
        path: '/path2',
      },
    });

    const projects = await prisma.project.findMany({
      where: { userId },
    });

    expect(projects.length).toBe(2);
    projects.forEach((p) => expect(p.userId).toBe(userId));
  });

  test('should delete a project', async () => {
    const project = await prisma.project.create({
      data: {
        userId,
        name: 'Delete Test Project',
        path: '/delete/path',
      },
    });

    const deleted = await prisma.project.delete({
      where: { id: project.id, userId },
    });

    expect(deleted.id).toBe(project.id);

    const stillExists = await prisma.project.findUnique({
      where: { id: project.id, userId },
    });

    expect(stillExists).toBeNull();
  });

  test('should update a project', async () => {
    const project = await prisma.project.create({
      data: {
        userId,
        name: 'Update Test Project',
        path: '/update/path',
        status: 'pending',
      },
    });

    const updated = await prisma.project.update({
      where: { id: project.id, userId },
      data: {
        name: 'Updated Name',
        status: 'completed',
      },
    });

    expect(updated.name).toBe('Updated Name');
    expect(updated.status).toBe('completed');
  });
});
