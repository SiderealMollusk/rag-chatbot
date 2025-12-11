import Link from 'next/link';
import { ReactNode } from 'react';
import './globals.css';

const MENU_ITEMS = [
  { name: 'Data Explorer', href: '/explorer' },
  { name: 'Timeline', href: '/timeline', disabled: false },
  { name: 'Job Supervisor', href: '/jobs', disabled: false },
  { name: 'Characters', href: '/characters', disabled: true },
  { name: 'Locations', href: '/locations', disabled: true },
  { name: 'Graph View', href: '/graph', disabled: true },
];

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="flex h-screen bg-neutral-900 text-neutral-100 font-sans antialiased">
        {/* Sidebar */}
        <aside className="w-64 border-r border-neutral-800 bg-black flex flex-col shrink-0">
          <div className="p-6 border-b border-neutral-800">
            <h1 className="text-xl font-bold tracking-wider text-amber-500">MOVIE BIBLE</h1>
            <p className="text-xs text-neutral-500 mt-1">Project: A Fire Upon the Deep</p>
          </div>

          <nav className="flex-1 p-4 space-y-1">
            {MENU_ITEMS.map((item) => (
              <div key={item.name}>
                {item.disabled ? (
                  <span className="block px-4 py-2 rounded text-neutral-600 cursor-not-allowed text-sm font-medium">
                    {item.name}
                  </span>
                ) : (
                  <Link
                    href={item.href}
                    className="block px-4 py-2 rounded hover:bg-neutral-800 hover:text-amber-400 transition-colors text-sm font-medium"
                  >
                    {item.name}
                  </Link>
                )}
              </div>
            ))}
          </nav>

          <div className="p-4 border-t border-neutral-800">
            <div className="text-xs text-neutral-600">
              v0.1.0 Alpha
              <br />
              Dockerized Stack
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-neutral-900">
          {children}
        </main>
      </body>
    </html>
  );
}
