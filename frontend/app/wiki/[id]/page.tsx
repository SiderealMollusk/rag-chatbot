'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

type Appearance = {
    scene_id: string;
    chapter: string;
    summary: string;
    role: string;
    context: string;
};

type EntityDetail = {
    id: string;
    name: string;
    category: string;
    data: any;
    appearances: Appearance[];
};

async function fetchEntity(id: string) {
    const res = await fetch(`http://localhost:8000/entities/${id}`);
    if (!res.ok) throw new Error('Failed to fetch data');
    return res.json();
}

export default function WikiArticlePage() {
    const params = useParams();
    const id = params.id as string;

    const [entity, setEntity] = useState<EntityDetail | null>(null);
    // const [loading, setLoading] = useState(true); // Simplified for this demo

    useEffect(() => {
        if (id) {
            fetchEntity(id).then(setEntity).catch(console.error);
        }
    }, [id]);

    if (!entity) return <div className="p-8 text-neutral-500">Loading neural archives...</div>;

    const metadata = entity.data || {};

    return (
        <div className="p-8 h-full flex flex-col max-w-5xl mx-auto">
            {/* Header */}
            <header className="mb-8 border-b border-neutral-800 pb-8">
                <Link href="/explorer" className="text-amber-500 hover:text-amber-400 text-sm mb-4 inline-block">&larr; Back to Explorer</Link>
                <div className="flex items-center gap-4">
                    <h1 className="text-5xl font-bold text-white tracking-tight">{entity.name}</h1>
                    <span className="px-3 py-1 rounded-full border border-neutral-700 text-neutral-400 text-sm uppercase tracking-wider">
                        {entity.category}
                    </span>
                </div>
                {metadata.significance && (
                    <p className="text-xl text-neutral-300 mt-4 font-serif italic border-l-4 border-amber-500 pl-4 py-1">
                        "{metadata.significance}"
                    </p>
                )}
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Main Content (Left) */}
                <div className="md:col-span-2 space-y-8">

                    {/* Description Section */}
                    <section>
                        <h2 className="text-lg font-bold text-white uppercase tracking-widest mb-4 border-b border-neutral-800 pb-2">Identity Matrix</h2>
                        <div className="bg-neutral-900 rounded-lg p-6 border border-neutral-800">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs text-neutral-500 uppercase">Aliases</label>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {metadata.aliases?.length ? metadata.aliases.map((a: string) => (
                                            <span key={a} className="bg-neutral-800 text-neutral-300 px-2 py-1 rounded text-sm">{a}</span>
                                        )) : <span className="text-neutral-600 italic">None registered</span>}
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs text-neutral-500 uppercase">Status</label>
                                    <div className="mt-1 text-neutral-300">
                                        {metadata.status || "Unknown"}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Appearances / Chronology */}
                    <section>
                        <h2 className="text-lg font-bold text-white uppercase tracking-widest mb-4 border-b border-neutral-800 pb-2">Chronology ({entity.appearances.length})</h2>
                        <div className="space-y-4">
                            {entity.appearances.map((app, i) => (
                                <Link
                                    href={`/timeline/${encodeURIComponent(app.chapter)}`}
                                    key={app.scene_id}
                                    className="block group bg-neutral-900/50 border border-neutral-800 hover:border-amber-500/50 p-4 rounded transition-all"
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <span className="text-xs text-amber-500 font-mono uppercase">
                                                {app.chapter}
                                                <span className="text-neutral-600 mx-2">//</span>
                                                Scene {app.scene_id.split('_').pop()}
                                            </span>
                                            <p className="text-neutral-300 mt-1 group-hover:text-white transition-colors">
                                                {app.summary}
                                            </p>
                                        </div>
                                        <span className="text-[10px] bg-neutral-800 text-neutral-500 px-2 py-1 rounded uppercase min-w-fit ml-4">
                                            {app.role}
                                        </span>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </section>
                </div>

                {/* Sidebar (Right) - Stats/Meta */}
                <div className="space-y-6">
                    <div className="bg-black/30 p-6 rounded border border-neutral-800">
                        <h3 className="text-sm font-bold text-neutral-400 uppercase mb-4">Neural Graph</h3>
                        <div className="text-center py-8">
                            <div className="text-4xl font-light text-white mb-2">{entity.appearances.length}</div>
                            <div className="text-xs text-neutral-500 uppercase tracking-widest">Total Scenes</div>
                        </div>
                        {/* Could add 'Most frequent co-occurrents' here later */}
                    </div>
                </div>
            </div>
        </div>
    );
}
