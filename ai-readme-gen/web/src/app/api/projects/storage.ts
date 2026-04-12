import { PrismaClient } from '@prisma/client';
import { generateApiKey } from '@/lib/auth';

const prisma = new PrismaClient();

export interface Project {
  id: string;
  userId: string;
  name: string;
  path: string;
  status: 'pending' | 'analyzing' | 'completed' | 'error';
  readmePath?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * Initialize storage (create default project if none exists)
 */
export async function initializeStorage(userId: string): Promise<Project[]> {
  const existingProjects = await prisma.project.findMany({
    where: { userId },
  });

  if (existingProjects.length === 0) {
    await prisma.project.create({
      data: {
        userId,
        name: 'Demo Project',
        path: '/demo/path',
        status: 'completed',
        readmePath: '/demo/readme.md',
      },
    });
  }

  return await prisma.project.findMany({
    where: { userId },
    orderBy: { createdAt: 'desc' },
  });
}

/**
 * Get a project by ID
 */
export async function getProject(id: string, userId: string): Promise<Project | null> {
  return prisma.project.findUnique({
    where: { id, userId },
  });
}

/**
 * Get all projects for a user
 */
export async function getAllProjects(userId: string): Promise<Project[]> {
  return prisma.project.findMany({
    where: { userId },
    orderBy: { createdAt: 'desc' },
  });
}

/**
 * Create a new project
 */
export async function createProject(name: string, path: string, userId: string): Promise<Project> {
  return prisma.project.create({
    data: {
      userId,
      name,
      path,
      status: 'pending',
    },
  });
}

/**
 * Delete a project
 */
export async function deleteProject(id: string, userId: string): Promise<boolean> {
  const result = await prisma.project.delete({
    where: { id, userId },
  });

  return result.id !== undefined;
}

/**
 * Update a project
 */
export async function updateProject(id: string, updates: Partial<Project>, userId: string): Promise<Project | null> {
  return prisma.project.update({
    where: { id, userId },
    data: updates,
  });
}
