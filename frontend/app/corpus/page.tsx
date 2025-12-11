'use client';

import { useState, useEffect, useRef } from 'react';

type TextChunk = {
    id: string;
    content: string;
    source_file: string;
    chapter_title: string;
    scene_index: number;
    paragraph_index: number;
    location_name: string;
    primary_characters: string;
    tags: string;
};

export default function CorpusPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<TextChunk[]>([]);
    const [total, setTotal] = useState(0);
    const [limit, setLimit] = useState(20);
    const [loading, setLoading] = useState(false);
    const debounceRef = useRef<NodeJS.Timeout | null>(null);

    const performSearch = async (q: string, newLimit: number) => {
        setLoading(true);
        try {
            const encodedQ = encodeURIComponent(q);
            const url = q
                ? `http://localhost:8000/corpus/search?q=${encodedQ}&limit=${newLimit}`
                : `http://localhost:8000/corpus/search?limit=${newLimit}`;

            const res = await fetch(url);
            if (!res.ok) throw new Error('Search failed');
            const data = await res.json();

            // Backend now returns { total: number, results: [] }
            setResults(data.results);
            setTotal(data.total);

        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        performSearch('', limit);
    }, []);

    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setQuery(val);
        setLimit(20); // Reset limit on new search

        if (debounceRef.current) clearTimeout(debounceRef.current);

        debounceRef.current = setTimeout(() => {
            performSearch(val, 20);
        }, 300);
    };

    const loadMore = () => {
        const newLimit = limit + 50;
        setLimit(newLimit);
        performSearch(query, newLimit);
    };

    return (
        <div className="min-h-screen bg-neutral-950 text-neutral-200 p-8">
            <div className="max-w-5xl mx-auto">
                <header className="mb-10">
                    <h1 className="text-4xl font-light text-white mb-2">Corpus Browser</h1>
                    <p className="text-neutral-500 mb-6">Search across the entire processed text of the book.</p>

                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg className="h-5 w-5 text-neutral-500 group-focus-within:text-amber-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <input
                            type="text"
                            className="block w-full pl-10 pr-3 py-4 border border-neutral-800 rounded-lg leading-5 bg-neutral-900 text-neutral-100 placeholder-neutral-500 focus:outline-none focus:bg-neutral-800 focus:ring-1 focus:ring-amber-500 focus:border-amber-500 sm:text-lg transition-all shadow-xl"
                            placeholder="Search for quotes, locations, or concepts (e.g. 'flenser', 'ice', 'scared')..."
                            value={query}
                            onChange={handleSearch}
                        />
                        {loading && (
                            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                                <svg className="animate-spin h-5 w-5 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            </div>
                        )}
                    </div>
                </header>

                <div className="flex justify-between items-center mb-6">
                    <div className="text-sm text-neutral-400">
                        {total > 0 && (
                            <>
                                Showing <span className="text-white font-mono">{results.length}</span> of <span className="text-white font-mono">{total}</span> segments
                            </>
                        )}
                    </div>
                </div>

                <div className="space-y-4">
                    {results.length === 0 && !loading && (
                        <div className="text-center py-20 text-neutral-600">
                            No matching text found.
                        </div>
                    )}

                    {results.map((chunk) => (
                        <div key={chunk.id} className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-6 hover:border-neutral-700 transition-all">

                            {/* Metadata Header */}
                            <div className="flex flex-wrap gap-2 mb-3 text-xs tracking-wide">
                                <span className="bg-amber-900/30 text-amber-500 px-2 py-1 rounded border border-amber-900/50">
                                    {chunk.chapter_title}
                                </span>
                                <span className="bg-neutral-800 text-neutral-400 px-2 py-1 rounded border border-neutral-700">
                                    Scene {chunk.scene_index}
                                </span>
                                {chunk.location_name && (
                                    <span className="bg-indigo-900/30 text-indigo-400 px-2 py-1 rounded border border-indigo-900/50">
                                        📍 {chunk.location_name}
                                    </span>
                                )}
                            </div>

                            {/* Content */}
                            <p className="text-neutral-200 text-lg leading-relaxed font-serif mb-4">
                                {chunk.content}
                            </p>

                            {/* Footer Tags */}
                            <div className="flex flex-wrap gap-2 items-center text-xs border-t border-neutral-800 pt-3 mt-2">
                                <span className="text-neutral-500 font-semibold mr-2">CONTEXT:</span>
                                {chunk.primary_characters.split(',').filter(Boolean).map((char, i) => (
                                    <span key={i} className="text-neutral-400 hover:text-white transition-colors cursor-default">
                                        {char.trim()}
                                    </span>
                                ))}

                                {chunk.tags && (
                                    <>
                                        <div className="w-1 h-1 bg-neutral-700 rounded-full mx-1"></div>
                                        {chunk.tags.split(',').filter(Boolean).map((tag, i) => (
                                            <span key={`tag-${i}`} className="text-emerald-500/70">
                                                #{tag.trim()}
                                            </span>
                                        ))}
                                    </>
                                )}

                                <span className="ml-auto text-neutral-600 font-mono text-[10px]">
                                    {chunk.id}
                                </span>
                            </div>
                        </div>
                    ))}

                    {results.length < total && (
                        <div className="pt-8 text-center">
                            <button
                                onClick={loadMore}
                                disabled={loading}
                                className="bg-neutral-800 hover:bg-neutral-700 text-neutral-300 px-6 py-3 rounded border border-neutral-700 transition-colors disabled:opacity-50"
                            >
                                {loading ? 'Loading...' : 'Load More Segments'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
