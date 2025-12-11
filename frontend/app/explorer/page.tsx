'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

// Types (should arguably be in a separate file)
type Entity = {
    id: string;
    name: string;
    category: string;
    data: any;
};

// Simple fetcher
async function fetchEntities() {
    const res = await fetch('http://localhost:8000/entities');
    if (!res.ok) throw new Error('Failed to fetch data');
    return res.json();
}

export default function ExplorerPage() {
    const [entities, setEntities] = useState<Entity[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState<string>('All');
    const [search, setSearch] = useState('');

    useEffect(() => {
        fetchEntities().then(data => {
            setEntities(data);
            setLoading(false);
        });
    }, []);

    // Derived state
    const categories = ['All', ...Array.from(new Set(entities.map(e => e.category)))];

    const filtered = entities.filter(e => {
        const matchesCat = selectedCategory === 'All' || e.category === selectedCategory;
        const matchesSearch = e.name.toLowerCase().includes(search.toLowerCase());
        return matchesCat && matchesSearch;
    });

    return (
        <div className="p-8 h-full flex flex-col">
            <header className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-light text-white">Data Explorer</h1>
                    <p className="text-neutral-500 mt-1">Browse all extracted knowledge nodes.</p>
                </div>

                <div className="flex space-x-4">
                    {/* Search */}
                    <input
                        type="text"
                        placeholder="Search entities..."
                        className="bg-neutral-800 border border-neutral-700 text-white px-3 py-2 rounded focus:outline-none focus:border-amber-500 transition-colors"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />

                    {/* Filter */}
                    <select
                        className="bg-neutral-800 border border-neutral-700 text-white px-3 py-2 rounded focus:outline-none focus:border-amber-500"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                </div>
            </header>

            {/* Grid */}
            <div className="flex-1 overflow-auto">
                {loading ? (
                    <div className="text-neutral-500 animate-pulse">Loading neural network...</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filtered.map(entity => (
                            <Link
                                href={`/wiki/${entity.id}`}
                                key={entity.id}
                                className="bg-neutral-800/50 border border-neutral-800 p-4 rounded hover:border-amber-500/50 transition-colors group block"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-neutral-200 group-hover:text-amber-400">{entity.name}</h4>
                                    <span className="text-[10px] uppercase tracking-wider bg-neutral-900 text-neutral-500 px-2 py-1 rounded">
                                        {entity.category}
                                    </span>
                                </div>
                                <p className="text-sm text-neutral-400 line-clamp-2">
                                    {entity.data?.significance || "No description available."}
                                </p>
                                <div className="mt-4 flex gap-2">
                                    {entity.data?.aliases?.map((alias: string) => (
                                        <span key={alias} className="text-xs text-neutral-600 bg-neutral-900/50 px-1 rounded">
                                            {alias}
                                        </span>
                                    ))}
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
