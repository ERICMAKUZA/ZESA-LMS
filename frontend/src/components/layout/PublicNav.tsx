'use client'

import Link from 'next/link'
import { useOptionalAuth } from '@/hooks/useOptionalAuth'

export default function PublicNav() {
  const { user } = useOptionalAuth()

  return (
    <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="flex flex-col leading-tight">
          <span className="text-lg font-extrabold text-primary tracking-tight">ZESA NTC</span>
          <span className="text-[10px] font-medium text-gray-400 tracking-wide uppercase">
            National Training Centre
          </span>
        </Link>
        <nav className="flex items-center gap-4 sm:gap-6">
          <Link
            href="/courses"
            className="hidden sm:block text-sm font-medium text-gray-600 hover:text-primary transition-colors"
          >
            Courses &amp; Schedule
          </Link>
          <a
            href="#faq"
            className="hidden sm:block text-sm font-medium text-gray-600 hover:text-primary transition-colors"
          >
            FAQ
          </a>
          <Link
            href="/track"
            className="hidden sm:block text-sm font-medium text-gray-600 hover:text-primary transition-colors"
          >
            Track Application
          </Link>
          {user ? (
            <Link
              href="/dashboard"
              className="text-sm font-semibold text-primary hover:text-primary-dark transition-colors"
            >
              My Portal →
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-medium text-gray-600 hover:text-primary transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="rounded-lg border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-white transition-colors"
              >
                Apply Now
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
