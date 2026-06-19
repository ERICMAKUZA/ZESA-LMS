import axios, { type AxiosRequestConfig } from 'axios'
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let pendingQueue: Array<{
  resolve: (value: string) => void
  reject: (reason: unknown) => void
}> = []

function flushQueue(error: unknown, token: string | null) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token!)
    }
  })
  pendingQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original: AxiosRequestConfig & { _retry?: boolean } = error.config
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      clearTokens()
      return Promise.reject(error)
    }
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject })
      }).then((token) => {
        original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
        return api(original)
      })
    }
    original._retry = true
    isRefreshing = true
    try {
      const { data } = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL ?? '/api'}/auth/token/refresh/`,
        { refresh: refreshToken },
      )
      setTokens(data.access, refreshToken)
      flushQueue(null, data.access)
      original.headers = { ...original.headers, Authorization: `Bearer ${data.access}` }
      return api(original)
    } catch (refreshError) {
      flushQueue(refreshError, null)
      clearTokens()
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export default api
