'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ArrowRight, MapPin, BookOpen } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import type { ApplicationStatus } from '@/types'

interface HistoryEntry {
  from_status: ApplicationStatus | null
  to_status: ApplicationStatus
  changed_at: string
  notes: string
}

interface TrackResult {
  ref: string
  status: ApplicationStatus
  status_display: string
  course_name: string | null
  assigned_centre: string | null
  last_updated: string | null
  history: HistoryEntry[]
}

export default function TrackPage({ params }: { params: { ref: string } }) {
  const [data, setData] = useState<TrackResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? ''
    fetch(`${apiBase}/api/track/${params.ref}/`)
      .then(async (res) => {
        if (res.status === 404) { setNotFound(true); return }
        const json = await res.json()
        setData(json)
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false))
  }, [params.ref])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* minimal header */}
      <header className="border-b border-gray-100 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link href="/" className="flex flex-col leading-tight">
            <span className="text-base font-extrabold text-primary tracking-tight">ZESA NTC</span>
            <span className="text-[9px] font-medium text-gray-400 tracking-wide uppercase">National Training Centre</span>
          </Link>
          <Link href="/login" className="text-sm font-medium text-primary hover:underline">
            Sign In
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-10">
        {loading && (
          <div className="flex justify-center py-20">
            <Spinner size="lg" className="text-primary" />
          </div>
        )}

        {!loading && notFound && (
          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center">
            <p className="text-4xl mb-4">🔍</p>
            <h1 className="text-xl font-bold text-gray-900">Application not found</h1>
            <p className="mt-2 text-sm text-gray-500">
              No application matching <span className="font-mono font-semibold">{params.ref}</span> was found.
              Double-check the reference number on your confirmation email.
            </p>
            <Link href="/" className="mt-6 inline-block text-sm font-medium text-primary hover:underline">
              Return to home
            </Link>
          </div>
        )}

        {!loading && data && (
          <div className="flex flex-col gap-6">
            {/* ref + status hero */}
            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">Reference number</p>
              <h1 className="text-3xl font-extrabold text-gray-900 font-mono">{data.ref}</h1>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <Badge status={data.status} className="text-sm px-3 py-1" />
                {data.last_updated && (
                  <span className="text-xs text-gray-400">
                    Last updated {format(new Date(data.last_updated), 'dd MMM yyyy HH:mm')}
                  </span>
                )}
              </div>
            </div>

            {/* course + centre */}
            <div className="rounded-xl border border-gray-200 bg-white p-6 flex flex-col gap-4">
              {data.course_name && (
                <div className="flex items-start gap-3">
                  <BookOpen className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                  <div>
                    <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Course</p>
                    <p className="text-sm font-semibold text-gray-800">{data.course_name}</p>
                  </div>
                </div>
              )}
              {data.assigned_centre && (
                <div className="flex items-start gap-3">
                  <MapPin className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                  <div>
                    <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Assigned Centre</p>
                    <p className="text-sm font-semibold text-gray-800">{data.assigned_centre}</p>
                  </div>
                </div>
              )}
            </div>

            {/* history timeline */}
            {data.history.length > 0 && (
              <div className="rounded-xl border border-gray-200 bg-white p-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Status history</h2>
                <ol className="relative ml-3 border-l border-gray-200 flex flex-col gap-6">
                  {data.history.map((entry, i) => (
                    <li key={i} className="ml-5">
                      <span className="absolute -left-2 flex h-4 w-4 items-center justify-center rounded-full bg-primary ring-4 ring-white" />
                      <div className="flex flex-wrap items-center gap-2">
                        {entry.from_status ? (
                          <>
                            <Badge status={entry.from_status} />
                            <ArrowRight className="h-3 w-3 text-gray-400" />
                          </>
                        ) : null}
                        <Badge status={entry.to_status} />
                      </div>
                      <p className="mt-1 text-xs text-gray-400">
                        {format(new Date(entry.changed_at), 'dd MMM yyyy HH:mm')}
                        {entry.notes && ` · ${entry.notes}`}
                      </p>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            <p className="text-center text-xs text-gray-400">
              Need help?{' '}
              <a href="mailto:admissions@zntc.ac.zw" className="text-primary hover:underline">
                admissions@zntc.ac.zw
              </a>
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
