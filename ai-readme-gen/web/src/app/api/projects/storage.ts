/**
 * LocalStorage-based project storage for ai-readme-gen
 * No authentication required - all data stored locally in browser
 */

interface Project {
  id: string;
  name: string;
  path: string;
  status: "pending" | "analyzing" | "completed" | "error";
  readmePath?: string;
  createdAt: string;
  updatedAt: string;
}

const STORAGE_KEY = "ai-readme-gen-projects";

/**
 * Initialize storage with default project if none exists
 */
export async function initializeStorage(): Promise<Project[]> {
  const existingProjects = await getAllProjects();

  if (existingProjects.length === 0) {
    const demoProject: Project = {
      id: `proj_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      name: "Demo Project",
      path: "/demo/path",
      status: "completed",
      readmePath: "/demo/readme.md",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await saveProjects([demoProject]);
  }

  return await getAllProjects();
}

/**
 * Get a project by ID
 */
export async function getProject(id: string): Promise<Project | null> {
  const projects = await getAllProjects();
  return projects.find((p) => p.id === id) || null;
}

/**
 * Get all projects
 */
export async function getAllProjects(): Promise<Project[]> {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) {
      return [];
    }
    return JSON.parse(data);
  } catch {
    return [];
  }
}

/**
 * Create a new project
 */
export async function createProject(name: string, path: string): Promise<Project> {
  const projects = await getAllProjects();
  const newProject: Project = {
    id: `proj_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name,
    path,
    status: "pending",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  await saveProjects([...projects, newProject]);
  return newProject;
}

/**
 * Delete a project
 */
export async function deleteProject(id: string): Promise<boolean> {
  const projects = await getAllProjects();
  const filtered = projects.filter((p) => p.id !== id);
  if (filtered.length === projects.length) {
    return false;
  }
  await saveProjects(filtered);
  return true;
}

/**
 * Update a project
 */
export async function updateProject(
  id: string,
  updates: Partial<Project>
): Promise<Project | null> {
  const projects = await getAllProjects();
  const index = projects.findIndex((p) => p.id === id);
  if (index === -1) {
    return null;
  }
  const updated = {
    ...projects[index],
    ...updates,
    updatedAt: new Date().toISOString(),
  };
  await saveProjects(projects.map((p, i) => (i === index ? updated : p)));
  return updated;
}

/**
 * Save projects array to localStorage
 */
async function saveProjects(projects: Project[]): Promise<void> {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
  } catch (error) {
    console.error("Failed to save projects to localStorage:", error);
    throw error;
  }
}
