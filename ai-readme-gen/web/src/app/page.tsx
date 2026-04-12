export default function Home() {
  return (
    <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your projects and generate AI-powered documentation
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="p-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-md text-white">
            <div className="text-3xl font-bold">3</div>
            <p className="text-blue-100 mt-1">Total Projects</p>
          </div>

          <div className="p-6 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-md text-white">
            <div className="text-3xl font-bold">1</div>
            <p className="text-purple-100 mt-1">Completed</p>
          </div>

          <div className="p-6 bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-md text-white">
            <div className="text-3xl font-bold">2</div>
            <p className="text-green-100 mt-1">In Progress</p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 border border-gray-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Quick Actions</h2>
            <a
              href="/projects/new"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Create New Project
            </a>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Select an existing project from the Projects page to generate documentation
          </p>
        </div>
      </div>
    </main>
  );
}
