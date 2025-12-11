'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

type Chapter = {
    title: str;
    scene_count: number;
    first_scene_id: string;
};

async function fetchChapters() {
    const res = await fetch('http://localhost:8000/chapters');
    if (!res.ok) throw new Error('Failed to fetch data');
    return res.json();
}

export default function TimelinePage() {
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchChapters().then(data => {
            setChapters(data);
            setLoading(false);
        });
    }, []);

    return (
        <div className="p-8 h-full flex flex-col">
            <header className="mb-8">
                <h1 className="text-3xl font-light text-white">Timeline</h1>
                <p className="text-neutral-500 mt-1">Sequential narrative breakdown by Chapter.</p>
            </header>

            {loading ? (
                <div className="text-neutral-500 animate-pulse">Loading timeline...</div>
            ) : (
                <div className="grid gap-4">
                    {chapters.map((chapter, index) => (
                        <Link
                            key={chapter.title}
                            href={`/timeline/${encodeURIComponent(chapter.title)}`}
                            className="block bg-neutral-800 border-l-4 border-amber-500/0 hover:border-amber-500 p-6 rounded hover:bg-neutral-800/80 transition-all group"
                        >
                            <div className="flex justify-between items-center">
                                <div>
                                    <span className="text-xs text-neutral-500 uppercase tracking-widest font-mono">
                                        Chapter {index + 1}
                                    </span>
                                    <h3 className="text-xl font-medium text-neutral-200 group-hover:text-white mt-1 capitalize">
                                        {chapter.title}
                                    </h3>
                                </div>
                                <div className="text-right">
                                    <span className="text-2xl font-light text-neutral-400 group-hover:text-amber-500">
                                        {chapter.scene_count}
                                    </span>
                                    <span className="text-xs text-neutral-600 block uppercase">Scenes</span>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
