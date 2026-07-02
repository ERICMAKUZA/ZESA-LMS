'use client'

import { useState, useEffect, type ReactNode } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard, FileText, BookOpen, Users, BarChart2, Menu, X, LogOut, User,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '@/hooks/useAuth'
import AuthGuard from '@/components/AuthGuard'
import { useToast } from '@/components/ui/Toast'

const nav = [
  { href: '/admin',              label: 'Dashboard',     icon: LayoutDashboard },
  { href: '/admin/applications', label: 'Applications',  icon: FileText },
  { href: '/admin/courses',      label: 'Courses',        icon: BookOpen },
  { href: '/admin/users',        label: 'Users',          icon: Users },
  { href: '/admin/reports',      label: 'Reports',        icon: BarChart2 },
]

const roleColor: Record<string, string> = {
  ADMIN:     'bg-primary/10 text-primary',
  REVIEWER:  'bg-yellow-100 text-yellow-800',
  SUPERADMIN:'bg-purple-100 text-purple-700',
  FINANCE:   'bg-teal-100 text-teal-700',
}

function AdminContent({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const { toast } = useToast()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (user && user.role === 'STUDENT') {
      toast({ variant: 'error', title: "You don't have access to that area." })
      router.push('/dashboard')
    }
  }, [user, router, toast])

  if (user?.role === 'STUDENT') return null

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-primary-dark text-white transition-transform duration-200',
          open ? 'translate-x-0' : '-translate-x-full',
          'lg:static lg:translate-x-0',
        )}
      >
        <div className="flex items-center gap-2 px-6 py-5 border-b border-white/10">
          <span className="text-lg font-bold tracking-tight">NTC Admin</span>
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
                pathname === href || (href !== '/admin' && pathname.startsWith(href))
                  ? 'bg-white/10 text-white'
                  : 'text-white/70 hover:bg-white/10 hover:text-white',
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>

      {open && (
        <div className="fixed inset-0 z-20 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-4 lg:px-6">
          <button className="lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="h-5 w-5 text-gray-600" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            {user?.role && (
              <span className={clsx('rounded-full px-2 py-0.5 text-xs font-semibold', roleColor[user.role] ?? 'bg-gray-100 text-gray-700')}>
                {user.role}
              </span>
            )}
            <User className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">{user?.full_name}</span>
            <button onClick={logout} title="Logout" className="rounded p-1.5 hover:bg-gray-100">
              <LogOut className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <AdminContent>{children}</AdminContent>
    </AuthGuard>
  )
}
