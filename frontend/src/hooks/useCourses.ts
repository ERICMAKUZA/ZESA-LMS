'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Course, PaginatedResponse } from '@/types'

export function useCourses() {
  return useQuery<PaginatedResponse<Course>>({
    queryKey: ['courses'],
    queryFn: async () => {
      const { data } = await api.get('/courses/')
      return data
    },
  })
}

export function useCourse(id: string | number) {
  return useQuery<Course>({
    queryKey: ['courses', id],
    queryFn: async () => {
      const { data } = await api.get(`/courses/${id}/`)
      return data
    },
    enabled: !!id,
  })
}
