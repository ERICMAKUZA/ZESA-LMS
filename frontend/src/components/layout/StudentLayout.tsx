'use client'

import { useState, type ReactNode } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard, BookOpen, FileText, Award, Menu, X, LogOut, User,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '@/hooks/useAuth'
import AuthGuard from '@/components/AuthGuard'

const nav = [
  { href: '/dashboard',      label: 'Dashboard',      icon: LayoutDashboard },
  { href: '/courses',        label: 'Browse Courses',  icon: BookOpen },
  { href: '/applications',   label: 'My Applications', icon: FileText },
  { href: '/certificates',   label: 'Certificates',    icon: Award },
]

export default function StudentLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-primary text-white transition-transform duration-200',
          open ? 'translate-x-0' : '-translate-x-full',
          'lg:static lg:translate-x-0',
        )}
      >
        <div className="flex items-center gap-2 px-6 py-5 border-b border-primary-light">
          <span className="text-lg font-bold tracking-tight">ZESA ILMP</span>
          <button className="ml-auto lg:hidden" onClick={() => setOpen(false)}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={clsx(
                'flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors',
                pathname.startsWith(href)
                  ? 'bg-primary-light text-white'
                  : 'text-white/70 hover:bg-primary-light hover:text-white',
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 z-20 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-4 lg:px-6">
          <button className="lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="h-5 w-5 text-gray-600" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <User className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">{user?.full_name}</span>
            <button onClick={logout} title="Logout" className="rounded p-1.5 hover:bg-gray-100">
              <LogOut className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <AuthGuard>{children}</AuthGuard>
        </main>
      </div>
    </div>
  )
}
