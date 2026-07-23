'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { AdminEnrollmentListItem, PaginatedResponse } from '@/types'

interface AdminEnrollmentFilters {
  search?: string
}

export function useAdminEnrollments(filters?: AdminEnrollmentFilters) {
  return useQuery<PaginatedResponse<AdminEnrollmentListItem>>({
    queryKey: ['admin-enrollments', filters],
    queryFn: async () => {
      const { data } = await api.get('/admin/enrollments/', {
        params: { application__status: 'ENROLLED', search: filters?.search || undefined },
      })
      return data
    },
  })
}

export function useRetryEnrollment() {
  const queryClient = useQueryClient()
  return useMutation<unknown, Error, string>({
    mutationFn: async (enrollmentId) => {
      const { data } = await api.post(`/admin/enrollments/${enrollmentId}/retry/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-enrollments'] })
    },
  })
}

export function useSuspendEnrollment() {
  const queryClient = useQueryClient()
  return useMutation<unknown, Error, { id: string; reason: string }>({
    mutationFn: async ({ id, reason }) => {
      const { data } = await api.post(`/admin/enrollments/${id}/suspend/`, { reason })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-enrollments'] })
    },
  })
}

export function useReinstateEnrollment() {
  const queryClient = useQueryClient()
  return useMutation<unknown, Error, string>({
    mutationFn: async (enrollmentId) => {
      const { data } = await api.post(`/admin/enrollments/${enrollmentId}/reinstate/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-enrollments'] })
    },
  })
}
