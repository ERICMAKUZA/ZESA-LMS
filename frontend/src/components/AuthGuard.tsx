'use client'

import { useEffect, type ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Spinner from '@/components/ui/Spinner'

export default function AuthGuard({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push(`/login?next=${encodeURIComponent(pathname)}`)
    }
  }, [isLoading, user, router, pathname])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <Spinner size="lg" className="text-primary" />
      </div>
    )
  }

  if (!user) return null

  return <>{children}</>
}
