'use client'

import { createContext, useContext } from 'react'
import type { AuthUser } from '@/types'

export interface RegisterData {
  first_name: string
  last_name: string
  email: string
  employee_id?: string
  department?: string
  password: string
}

export interface AuthContextValue {
  user: AuthUser | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<AuthUser | null>
  logout: () => void
  register: (data: RegisterData) => Promise<unknown>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
