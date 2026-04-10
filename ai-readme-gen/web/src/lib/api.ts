/**
 * API client for communicating with the backend service.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Project {
  id: string;
  name: string;
  path: string;
  createdAt: string;
  updatedAt: string;
  status: "pending" | "analyzing" | "completed" | "error";
}

export interface AnalysisResult {
  readme: string;
  diagram: string;
  apiDocs: string;
  setup: string;
}

export interface AnalyzeRequest {
  path: string;
  model?: string;
}

export interface AnalyzeResponse {
  success: boolean;
  result?: AnalysisResult;
  error?: string;
}

export async function createProject(name: string, path: string): Promise<Project> {
  const response = await fetch(`${API_BASE_URL}/api/projects`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, path }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create project: ${response.statusText}`);
  }

  return response.json();
}

export async function listProjects(): Promise<Project[]> {
  const response = await fetch(`${API_BASE_URL}/api/projects`);

  if (!response.ok) {
    throw new Error(`Failed to list projects: ${response.statusText}`);
  }

  return response.json();
}

export async function analyzeProject(projectId: string, path: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ path }),
  });

  if (!response.ok) {
    throw new Error(`Failed to analyze project: ${response.statusText}`);
  }

  return response.json();
}

export async function getProject(projectId: string): Promise<Project | null> {
  const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}`);

  if (!response.ok) {
    return null;
  }

  return response.json();
}
