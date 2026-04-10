export default function ProjectsPage() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto p-8">
        <h1 className="text-3xl font-bold mb-8">Projects</h1>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border-2 border-dashed border-gray-300 dark:border-slate-600">
            <h2 className="text-xl font-semibold mb-4">New Project</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Create a new project to generate documentation
            </p>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
              Create Project
            </button>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Projects</h2>
            <p className="text-gray-500 dark:text-gray-500 italic">
              No projects yet
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
