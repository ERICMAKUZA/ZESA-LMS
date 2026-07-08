'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ChevronDown, ChevronUp, LogIn, ShieldCheck, GraduationCap } from 'lucide-react'
import Link from 'next/link'
import PublicLayout from '@/components/layout/PublicLayout'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

interface DemoAccount {
  label: string
  email: string
  role: string
}

interface DemoAccountsResponse {
  primary: DemoAccount[]
  all: DemoAccount[]
}

const DEMO_PASSWORD = 'Demo1234!'

const roleBadgeClass: Record<string, string> = {
  STUDENT:  'bg-blue-100 text-blue-700',
  REVIEWER: 'bg-yellow-100 text-yellow-800',
  ADMIN:    'bg-primary/10 text-primary',
  FINANCE:  'bg-teal-100 text-teal-700',
}

function LoginContent() {
  const { login } = useAuth()
  const { toast } = useToast()
  const router = useRouter()
  const searchParams = useSearchParams()
  const nextUrl = searchParams.get('next')

  const [loadingEmail, setLoadingEmail] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)
  const [showDemoAccounts, setShowDemoAccounts] = useState(false)

  // Form state
  const [formEmail, setFormEmail] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formLoading, setFormLoading] = useState(false)

  const { data: demoAccounts, isLoading: accountsLoading } = useQuery<DemoAccountsResponse>({
    queryKey: ['demo-accounts'],
    queryFn: async () => {
      const { data } = await api.get('/demo-accounts/')
      return data
    },
    staleTime: Infinity,
  })

  const redirectAfterLogin = (user: ReturnType<typeof useAuth>['user']) => {
    if (nextUrl) {
      router.push(nextUrl)
      return
    }
    const isAdmin = user && ['ADMIN', 'REVIEWER', 'SUPERADMIN', 'FINANCE', 'CENTRE_ADMIN', 'LECTURER'].includes(user.role)
    router.push(isAdmin ? '/admin' : '/dashboard')
  }

  const handleFormLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormLoading(true)
    try {
      const user = await login(formEmail.trim(), formPassword)
      toast({ variant: 'success', title: `Welcome back, ${user?.full_name ?? formEmail}` })
      redirectAfterLogin(user)
    } catch {
      toast({ variant: 'error', title: 'Sign in failed', description: 'Incorrect email or password.' })
    } finally {
      setFormLoading(false)
    }
  }

  const handleDemoLogin = async (email: string, role: string) => {
    setLoadingEmail(email)
    try {
      const user = await login(email, DEMO_PASSWORD)
      toast({ variant: 'success', title: `Signed in as ${user?.full_name ?? email}` })
      redirectAfterLogin(user)
    } catch {
      toast({ variant: 'error', title: 'Login failed', description: 'Could not sign in. Please try again.' })
    } finally {
      setLoadingEmail(null)
    }
  }

  const primary = demoAccounts?.primary ?? []
  const allAccounts = demoAccounts?.all ?? []

  const primaryIcons: Record<string, React.ReactNode> = {
    STUDENT:  <GraduationCap className="h-8 w-8 text-primary" />,
    REVIEWER: <ShieldCheck className="h-8 w-8 text-yellow-600" />,
  }

  return (
    <PublicLayout>
      <div className="flex min-h-[80vh] items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gray-900">ZESA National Training Centre</h1>
            <p className="mt-1 text-sm font-medium text-accent">Empowering Zimbabwe&apos;s Future Through Excellence</p>
          </div>

          {/* Main login form */}
          <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Sign in to your account</h2>
            <form onSubmit={handleFormLogin} className="flex flex-col gap-4">
              <Input
                label="Email address"
                type="email"
                autoComplete="email"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                required
              />
              <Input
                label="Password"
                type="password"
                autoComplete="current-password"
                value={formPassword}
                onChange={(e) => setFormPassword(e.target.value)}
                required
              />
              <Button type="submit" loading={formLoading} className="mt-1 w-full">
                Sign in
              </Button>
            </form>
            <p className="mt-5 text-center text-sm text-gray-600">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="font-medium text-primary hover:underline">Create one</Link>
            </p>
          </div>

          {/* Demo accounts — collapsible */}
          <div className="mt-4 rounded-xl border border-yellow-200 bg-yellow-50 overflow-hidden">
            <button
              onClick={() => setShowDemoAccounts((v) => !v)}
              className="flex w-full items-center justify-between px-5 py-3 text-sm font-medium text-yellow-800 hover:bg-yellow-100 transition-colors"
            >
              <span>DEMO — quick sign-in accounts</span>
              {showDemoAccounts ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showDemoAccounts && (
              <div className="border-t border-yellow-200 bg-white">
                {accountsLoading ? (
                  <div className="flex justify-center py-6">
                    <Spinner size="lg" className="text-primary" />
                  </div>
                ) : (
                  <>
                    <div className="grid gap-3 p-4 sm:grid-cols-2">
                      {primary.map((account) => (
                        <button
                          key={account.email}
                          onClick={() => handleDemoLogin(account.email, account.role)}
                          disabled={loadingEmail !== null}
                          className="group flex flex-col items-center gap-2 rounded-xl border-2 border-gray-200 bg-white p-4 text-center shadow-sm transition-all hover:border-primary hover:shadow-md disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-50 group-hover:bg-primary/5 transition-colors">
                            {loadingEmail === account.email
                              ? <Spinner size="lg" className="text-primary" />
                              : primaryIcons[account.role] ?? <LogIn className="h-7 w-7 text-gray-400" />
                            }
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 text-sm">{account.label}</p>
                            <p className="text-xs text-gray-400">{account.email}</p>
                          </div>
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${roleBadgeClass[account.role] ?? 'bg-gray-100 text-gray-700'}`}>
                            {account.role}
                          </span>
                        </button>
                      ))}
                    </div>

                    {allAccounts.length > 0 && (
                      <div className="border-t border-gray-100">
                        <button
                          onClick={() => setShowAll((v) => !v)}
                          className="flex w-full items-center justify-between px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                          <span>More accounts ({allAccounts.length})</span>
                          {showAll ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                        </button>
                        {showAll && (
                          <div className="border-t border-gray-100 divide-y divide-gray-100">
                            {allAccounts.map((account) => (
                              <div key={account.email} className="flex items-center gap-3 px-5 py-3">
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 truncate">{account.label}</p>
                                  <p className="text-xs text-gray-400 truncate">{account.email}</p>
                                </div>
                                <span className={`shrink-0 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${roleBadgeClass[account.role] ?? 'bg-gray-100 text-gray-700'}`}>
                                  {account.role}
                                </span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDemoLogin(account.email, account.role)}
                                  disabled={loadingEmail !== null}
                                  loading={loadingEmail === account.email}
                                >
                                  Login
                                </Button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </PublicLayout>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  )
}
