import Link from 'next/link'
import { type ReactNode } from 'react'

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-primary">ZESA ILMP</span>
          </Link>
          <nav className="flex items-center gap-6">
            <Link href="/courses" className="text-sm font-medium text-gray-600 hover:text-primary">
              Courses
            </Link>
            <Link href="/login" className="text-sm font-medium text-gray-600 hover:text-primary">
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-light"
            >
              Register
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-gray-200 py-6 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} Zimbabwe Electricity Supply Authority — ILMP
      </footer>
    </div>
  )
}
