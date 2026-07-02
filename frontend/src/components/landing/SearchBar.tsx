'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'

const SUGGESTIONS = ['Drone Piloting', 'Solar & Grid', 'Technical Skills', 'Leadership']

export default function SearchBar() {
  const [query, setQuery] = useState('')
  const router = useRouter()

  function submit(q: string) {
    if (!q.trim()) return
    router.push(`/courses?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <div className="relative z-10 -mt-10 mx-auto w-full max-w-3xl px-4">
      <div className="rounded-2xl bg-white shadow-xl p-4 md:p-6">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit(query)}
              placeholder="What do you want to learn?"
              className="w-full rounded-lg border border-gray-200 bg-gray-50 pl-10 pr-4 py-3 text-sm md:text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
            />
          </div>
          <button
            onClick={() => submit(query)}
            className="rounded-lg bg-primary hover:bg-primary-light text-white font-semibold px-5 py-3 text-sm md:text-base transition-colors whitespace-nowrap"
          >
            Search
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-gray-500 self-center">Quick:</span>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:border-primary hover:text-primary transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
