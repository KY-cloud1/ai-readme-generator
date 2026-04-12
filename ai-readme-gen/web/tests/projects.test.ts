import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';
import {
  createProject,
  getAllProjects,
  getProject,
  deleteProject,
  updateProject,
} from '../src/app/api/projects/storage';

describe('Projects (localStorage)', () => {
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

  afterEach(() => {
    mockStorage = {};
  });

  test('should create a new project', async () => {
    const project = await createProject('Test Project', '/test/path');
    expect(project.id).toBeDefined();
    expect(project.name).toBe('Test Project');
    expect(project.path).toBe('/test/path');
    expect(project.status).toBe('pending');
  });

  test('should get project by ID', async () => {
    const project = await createProject('Get Test Project', '/get/path');
    const foundProject = await getProject(project.id);
    expect(foundProject).toBeDefined();
    expect(foundProject?.name).toBe('Get Test Project');
  });

  test('should get all projects', async () => {
    await createProject('Project 1', '/path1');
    await createProject('Project 2', '/path2');
    const projects = await getAllProjects();
    expect(projects.length).toBe(2);
  });

  test('should delete a project', async () => {
    const project = await createProject('Delete Test Project', '/delete/path');
    const deleted = await deleteProject(project.id);
    expect(deleted).toBe(true);

    const stillExists = await getProject(project.id);
    expect(stillExists).toBeNull();
  });

  test('should update a project', async () => {
    const project = await createProject('Update Test Project', '/update/path');
    const updated = await updateProject(project.id, {
      name: 'Updated Name',
      status: 'completed',
    });

    expect(updated?.name).toBe('Updated Name');
    expect(updated?.status).toBe('completed');
  });

  });
