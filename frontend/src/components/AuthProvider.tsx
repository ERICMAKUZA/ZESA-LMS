'use client'

import { useState, useEffect, useCallback, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { getUser, setTokens, clearTokens } from '@/lib/auth'
import { AuthContext, type RegisterData } from '@/hooks/useAuth'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [user, setUser] = useState(getUser)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setUser(getUser())
    setIsLoading(false)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<{ access: string; refresh: string }>(
      '/auth/login/',
      { email, password },
    )
    setTokens(data.access, data.refresh)
    const decoded = getUser()
    // flushSync commits the user state synchronously so any subsequent
    // router navigation sees the correct role immediately (React 18
    // concurrent mode can otherwise start rendering the new page before
    // the batched state update is committed, causing stale-role redirects).
    flushSync(() => {
      setUser(decoded)
    })
    queryClient.clear()
    router.refresh()
    return decoded
  }, [queryClient, router])

  const logout = useCallback(() => {
    // Fire-and-forget audit hook — tokens are stateless, so logout is
    // really just discarding them client-side; this only records that it
    // happened. Must fire before clearTokens() so the JWT is still attached.
    api.post('/auth/logout/').catch(() => {})
    clearTokens()
    flushSync(() => {
      setUser(null)
    })
    queryClient.clear()
    router.refresh()
    router.push('/login')
  }, [router, queryClient])

  const register = useCallback(async (formData: RegisterData) => {
    const { data } = await api.post('/auth/register/', formData)
    return data
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}
