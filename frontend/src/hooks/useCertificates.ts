'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Certificate, PaginatedResponse } from '@/types'

export function useMyCertificates() {
  return useQuery<PaginatedResponse<Certificate>>({
    queryKey: ['my-certificates'],
    queryFn: async () => {
      const { data } = await api.get('/certs/')
      return data
    },
  })
}
