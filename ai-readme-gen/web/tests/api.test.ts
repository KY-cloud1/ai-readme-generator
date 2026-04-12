import { describe, test, expect, beforeEach } from '@jest/globals';
import { createProject, getAllProjects } from '../src/app/api/projects/storage';

describe('API Integration', () => {
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

  test('should create project via API pattern', async () => {
    const project = await createProject('API Test Project', '/api/test/path');
    expect(project.id).toBeDefined();
    expect(project.name).toBe('API Test Project');
  });

  test('should list projects via API pattern', async () => {
    await createProject('Project 1', '/path1');
    await createProject('Project 2', '/path2');
    const projects = await getAllProjects();
    expect(projects.length).toBe(2);
  });
});
