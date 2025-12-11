'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

type Mention = {
    id: string;
    name: string;
    category: string;
    role: string;
};

type Scene = {
    id: string;
    chapter_title: string;
    sequence_index: number;
    summary: string;
    location_id: string | null;
    mentions: Mention[];
};

async function fetchChapterScenes(title: string) {
    const res = await fetch(`http://localhost:8000/chapters/${title}/scenes`);
    if (!res.ok) throw new Error('Failed to fetch data');
    return res.json();
}

export default function ChapterDetailPage() {
    const params = useParams();
    // Decode because params.slug comes in encoded (e.g. "forty%20one")
    const slug = decodeURIComponent(params.slug as string);

    const [scenes, setScenes] = useState<Scene[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (slug) {
            fetchChapterScenes(slug).then(data => {
                setScenes(data);
                setLoading(false);
            });
        }
    }, [slug]);

    if (loading) return <div className="p-8 text-neutral-500">Loading chapter data...</div>;

    return (
        <div className="p-8 h-full flex flex-col max-w-5xl mx-auto">
            <header className="mb-8 border-b border-neutral-800 pb-8">
                <Link href="/timeline" className="text-amber-500 hover:text-amber-400 text-sm mb-4 inline-block">&larr; Back to Timeline</Link>
                <h1 className="text-4xl font-light text-white capitalize">{slug}</h1>
                <p className="text-neutral-500 mt-2">Breakdown of {scenes.length} scenes.</p>
            </header>

            <div className="space-y-12">
                {scenes.map((scene, index) => (
                    <div key={scene.id} className="relative pl-8 border-l border-neutral-800">
                        {/* Timeline Dot */}
                        <div className="absolute -left-[5px] top-0 w-[9px] h-[9px] rounded-full bg-neutral-600 ring-4 ring-neutral-900"></div>

                        <div className="mb-2 flex items-center gap-3">
                            <span className="text-xs font-mono text-neutral-500">SCENE {(index + 1).toString().padStart(2, '0')}</span>
                            {scene.location_id && (
                                <span className="bg-neutral-800 text-neutral-400 text-[10px] px-2 py-0.5 rounded uppercase tracking-wider">
                                    Location ID: {scene.location_id}
                                </span>
                            )}
                        </div>

                        <div className="bg-neutral-900/50 p-0 rounded-lg">
                            <p className="text-neutral-300 leading-relaxed text-lg mb-6 font-serif">
                                {scene.summary}
                            </p>

                            {/* Connected Elements */}
                            {scene.mentions.length > 0 && (
                                <div className="border-t border-neutral-800 pt-4">
                                    <h4 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">Connected Elements</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {scene.mentions.map(m => (
                                            <Link
                                                key={m.id}
                                                href={`/wiki/${m.id}`}
                                                className={`
                                                    text-xs px-2 py-1 rounded border border-neutral-800 hover:ring-1 hover:ring-opacity-50 transition-all cursor-pointer block
                                                    ${m.category === 'Character' ? 'text-blue-300 bg-blue-900/10 hover:ring-blue-400' : ''}
                                                    ${m.category === 'Location' ? 'text-green-300 bg-green-900/10 hover:ring-green-400' : ''}
                                                    ${m.category === 'Faction' ? 'text-red-300 bg-red-900/10 hover:ring-red-400' : ''}
                                                    ${m.category === 'Technology' ? 'text-purple-300 bg-purple-900/10 hover:ring-purple-400' : ''}
                                                `}
                                            >
                                                {m.name}
                                                {m.role !== 'APPEARANCE' && <span className="opacity-50 ml-1">({m.role.toLowerCase()})</span>}
                                            </Link>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
