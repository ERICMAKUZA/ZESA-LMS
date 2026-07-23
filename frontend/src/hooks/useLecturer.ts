'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { CourseSchedule, LecturerApplication, PaginatedResponse } from '@/types'

interface SignOffResponse {
  status: string
  lecturer_signed_off: boolean
  certificate_number: string | null
  message: string
}

export function useLecturerApplications() {
  return useQuery<PaginatedResponse<LecturerApplication>>({
    queryKey: ['lecturer-applications'],
    queryFn: async () => {
      const { data } = await api.get('/lecturer/applications/')
      return data
    },
  })
}

export function useLecturerSchedules() {
  return useQuery<CourseSchedule[]>({
    queryKey: ['lecturer-schedules'],
    queryFn: async () => {
      const { data } = await api.get('/courses/lecturer/schedules/')
      return data
    },
  })
}

export function useLecturerSignOff(id: string) {
  const queryClient = useQueryClient()
  return useMutation<SignOffResponse, Error, { notes?: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`/lecturer/applications/${id}/sign-off/`, payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lecturer-applications'] })
    },
  })
}
