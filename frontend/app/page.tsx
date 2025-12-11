export default function Home() {
  return (
    <div className="p-12 max-w-4xl mx-auto">
      <h2 className="text-4xl font-light text-white mb-6">Welcome to the Movie Bible.</h2>
      <p className="text-lg text-neutral-400 mb-8">
        This tool aggregates chapter analysis, extracted entities, and scene graphs into a coherent
        production database for adaptation planning.
      </p>

      <div className="grid grid-cols-2 gap-6">
        <div className="p-6 bg-neutral-800 rounded border border-neutral-700">
          <h3 className="text-xl font-bold text-amber-500 mb-2">Ingestion Status</h3>
          <div className="flex items-center space-x-2 text-green-400">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            <span>Database Online</span>
          </div>
          <p className="text-sm text-neutral-400 mt-2">
            44 Entities / 175 Scenes
          </p>
        </div>

        <div className="p-6 bg-neutral-800 rounded border border-neutral-700">
          <h3 className="text-xl font-bold text-amber-500 mb-2">Quick Actions</h3>
          <a href="/explorer" className="inline-block bg-neutral-700 hover:bg-neutral-600 text-white px-4 py-2 rounded text-sm transition-colors mr-3">
            Launch Data Explorer &rarr;
          </a>
          <a href="/corpus" className="inline-block bg-neutral-700 hover:bg-neutral-600 text-white px-4 py-2 rounded text-sm transition-colors">
            Browse Corpus &rarr;
          </a>
        </div>
      </div>
    </div>
  );
}
