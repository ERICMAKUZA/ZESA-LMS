'use client'

import { useState, useEffect, useCallback, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { getUser, setTokens, clearTokens } from '@/lib/auth'
import { AuthContext, type RegisterData } from '@/hooks/useAuth'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter()
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
    setUser(decoded)
    return decoded
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    router.push('/login')
  }, [router])

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
