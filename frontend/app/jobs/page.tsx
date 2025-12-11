"use client"

import { useState, useEffect } from 'react'

export default function JobsPage() {
    const [data, setData] = useState({ backlog: 0, metal: 0, cloud: 0, done: 0 })
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Assume API is proxied or using env var, but for localhost dev:
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/jobs/status`)
                const result = await response.json()
                setData(result)
                setLoading(false)
            } catch (e) {
                console.error("Failed to fetch job status", e)
            }
        }

        // Poll every 1s
        const interval = setInterval(fetchData, 1000)
        fetchData() // Initial fetch

        return () => clearInterval(interval)
    }, [])

    const cards = [
        { title: "Backlog", value: data.backlog, color: "text-red-400 border-red-900 bg-red-900/10" },
        { title: "Metal Queue", value: data.metal, color: "text-blue-400 border-blue-900 bg-blue-900/10" },
        { title: "Cloud Queue", value: data.cloud, color: "text-purple-400 border-purple-900 bg-purple-900/10" },
        { title: "Completed", value: data.done, color: "text-green-400 border-green-900 bg-green-900/10" },
    ]

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <h1 className="text-3xl font-bold text-center mb-12 text-zinc-300">Hybrid Job Supervisor</h1>

                {/* The Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                    {cards.map((card) => (
                        <div
                            key={card.title}
                            className={`aspect-square flex flex-col items-center justify-center border-2 rounded-2xl ${card.color} transition-all duration-300`}
                        >
                            <div className="text-6xl font-black">{loading ? '-' : card.value}</div>
                            <div className="text-sm uppercase tracking-widest mt-4 font-semibold opacity-80">{card.title}</div>
                        </div>
                    ))}
                </div>

                {/* Legend / Status */}
                <div className="text-center text-zinc-500 text-sm mt-12">
                    Syncing every 1s • Connected to Redis
                </div>
            </div>
        </div>
    )
}
