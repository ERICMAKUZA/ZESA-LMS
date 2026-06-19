import type { AuthUser } from '@/types'

const ACCESS_TOKEN_KEY = 'ilmp_access'
const REFRESH_TOKEN_KEY = 'ilmp_refresh'

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function getUser(): AuthUser | null {
  const token = getAccessToken()
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.email || !payload.role) {
      console.warn('[auth] JWT is missing expected claims (email/role). Token may be stale — re-login recommended.', payload)
    }
    return {
      id: payload.user_id,
      email: payload.email ?? '',
      full_name: payload.full_name ?? '',
      role: payload.role ?? 'STUDENT',
      employee_id: payload.employee_id ?? '',
    }
  } catch {
    return null
  }
}
