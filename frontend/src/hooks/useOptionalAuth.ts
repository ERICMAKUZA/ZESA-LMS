'use client'

import { useEffect, useState } from 'react'
import { getUser } from '@/lib/auth'
import type { AuthUser } from '@/types'

export function useOptionalAuth() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setUser(getUser())
    setLoading(false)
  }, [])

  return { user, loading }
}
