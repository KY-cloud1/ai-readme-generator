"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createProject, listProjects, Project, AnalysisResult } from "@/lib/api";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectPath, setNewProjectPath] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedAnalysisResult, setSelectedAnalysisResult] = useState<AnalysisResult | null>(null);

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      setGlobalError("Failed to fetch projects");
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName || !newProjectPath) {
      setCreateError("Please fill in all fields");
      return;
    }

    setLoading(true);
    setCreateError(null);

    try {
      const project = await createProject(newProjectName, newProjectPath);
      setProjects([...projects, project]);
      setNewProjectName("");
      setNewProjectPath("");
    } catch (err) {
      setCreateError("Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (projectId: string) => {
    setAnalyzing(true);
    setAnalyzeError(null);

    try {
      const result = await fetch(`${window.location.origin}/api/projects/${projectId}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          path: "/path/to/project",
        }),
      });

      if (!result.ok) {
        throw new Error("Analysis failed");
      }

      const data = await result.json();
      setSelectedAnalysisResult(data);
    } catch (err) {
      setAnalyzeError("Failed to analyze project");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Projects</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Manage your codebase analysis projects
            </p>
          </div>
          <button
            onClick={() => router.push("/projects/new")}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            New Project
          </button>
        </div>

        {/* Create Project Form */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 mb-8 border border-gray-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Create New Project</h2>
          {createError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
              <p className="text-red-600 dark:text-red-400 text-sm">{createError}</p>
            </div>
          )}
          <div className="grid md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Project name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="text"
              placeholder="Project path (e.g., /path/to/repo)"
              value={newProjectPath}
              onChange={(e) => setNewProjectPath(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="mt-4 flex gap-4">
            <button
              onClick={handleCreateProject}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Creating..." : "Create Project"}
            </button>
            <button
              onClick={() => {
                setNewProjectName("");
                setNewProjectPath("");
              }}
              className="px-6 py-2 bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Projects Grid */}
        {globalError && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-600 dark:text-red-400">{globalError}</p>
          </div>
        )}

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Project List */}
          {projects.map((project) => (
            <div
              key={project.id}
              className={`bg-white dark:bg-slate-800 rounded-lg shadow p-6 border ${
                project.status === "completed"
                  ? "border-green-200 dark:border-green-800"
                  : project.status === "analyzing"
                  ? "border-blue-200 dark:border-blue-800"
                  : "border-yellow-200 dark:border-yellow-800"
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">{project.name}</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {project.path}
                  </p>
                </div>
                <span className="px-2 py-1 text-xs rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300">
                  {project.status}
                </span>
              </div>

              <div className="space-y-2">
                <button
                  onClick={() => setSelectedProjectId(project.id)}
                  className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  View Results
                </button>
                {project.status !== "completed" && (
                  <button
                    onClick={() => {
                      handleAnalyze(project.id);
                      setSelectedProjectId(project.id);
                    }}
                    disabled={analyzing || selectedProjectId === project.id}
                    className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    {analyzing ? "Analyzing..." : selectedProjectId === project.id ? "Analyzing..." : "Analyze"}
                  </button>
                )}
              </div>
            </div>
          ))}

          {/* Results Panel */}
          {selectedProjectId && selectedAnalysisResult && (
            <div className="md:col-span-2 lg:col-span-3 bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Analysis Results for {projects.find(p => p.id === selectedProjectId)?.name || "Selected Project"}</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleCopy(selectedAnalysisResult.readme)}
                    className="px-3 py-1 bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 text-gray-900 dark:text-white rounded text-sm"
                  >
                    Copy README
                  </button>
                  <button
                    onClick={() =>
                      handleDownload(selectedAnalysisResult.readme, "README.md")
                    }
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
                  >
                    Download README
                  </button>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium mb-2">README.md</h3>
                  <pre className="bg-gray-100 dark:bg-slate-900 p-4 rounded-lg text-sm overflow-auto max-h-64">
                    {selectedAnalysisResult.readme}
                  </pre>
                </div>
                <div>
                  <h3 className="font-medium mb-2">Architecture Diagram</h3>
                  <pre className="bg-gray-100 dark:bg-slate-900 p-4 rounded-lg text-sm overflow-auto max-h-64">
                    {selectedAnalysisResult.diagram}
                  </pre>
                </div>
              </div>

              {selectedAnalysisResult.apiDocs && (
                <div className="mt-6">
                  <h3 className="font-medium mb-2">API Documentation</h3>
                  <pre className="bg-gray-100 dark:bg-slate-900 p-4 rounded-lg text-sm overflow-auto max-h-48">
                    {selectedAnalysisResult.apiDocs}
                  </pre>
                </div>
              )}

              {selectedAnalysisResult.setup && (
                <div className="mt-6">
                  <h3 className="font-medium mb-2">Setup Instructions</h3>
                  <pre className="bg-gray-100 dark:bg-slate-900 p-4 rounded-lg text-sm overflow-auto max-h-48">
                    {selectedAnalysisResult.setup}
                  </pre>
                </div>
              )}
            </div>
          )}
          {analyzeError && (
            <div className="md:col-span-2 lg:col-span-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
              <p className="text-red-600 dark:text-red-400">{analyzeError}</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}