'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import BrandLogo from '@/components/layout/BrandLogo'

export default function TrackIndexPage() {
  const [ref, setRef] = useState('')
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = ref.trim().toUpperCase()
    if (trimmed) router.push(`/track/${trimmed}`)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-100 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <Link href="/">
            <BrandLogo />
          </Link>
          <Link href="/login" className="text-sm font-medium text-primary hover:underline">
            Sign In
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-md px-4 py-20">
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900">Track your application</h1>
          <p className="mt-2 text-sm text-gray-500">
            Enter your reference number (e.g. <span className="font-mono font-semibold">ZNTC-2026-0001</span>)
          </p>
          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-3">
            <Input
              placeholder="ZNTC-YYYY-NNNN"
              value={ref}
              onChange={(e) => setRef(e.target.value)}
              className="text-center font-mono uppercase tracking-wider"
            />
            <Button type="submit" disabled={!ref.trim()}>
              Check status
            </Button>
          </form>
        </div>
      </main>
    </div>
  )
}
