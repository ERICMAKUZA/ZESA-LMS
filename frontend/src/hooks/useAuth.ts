'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { getUser, setTokens, clearTokens } from '@/lib/auth'
import type { AuthUser } from '@/types'

interface RegisterData {
  first_name: string
  last_name: string
  email: string
  employee_id?: string
  department?: string
  password: string
}

export function useAuth() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
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

  return { user, isLoading, login, logout, register }
}
