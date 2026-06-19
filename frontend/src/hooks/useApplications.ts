'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Application, ApplicationListItem, PaginatedResponse, DashboardStats } from '@/types'

interface ApplicationFilters {
  status?: string
  course?: string | number
  applicant__email?: string
  submitted_after?: string
  submitted_before?: string
  reviewer?: string | number
}

interface CreateApplicationData {
  course: number
  motivation: string
  line_manager_email: string
  department: string
  employee_id?: string
}

interface ReviewActionData {
  action: 'approve' | 'reject' | 'request_more_info'
  notes?: string
  rejection_reason?: string
}

export function useMyApplications() {
  return useQuery<PaginatedResponse<ApplicationListItem>>({
    queryKey: ['my-applications'],
    queryFn: async () => {
      const { data } = await api.get('/my-applications/')
      return data
    },
  })
}

export function useApplication(id: string) {
  return useQuery<Application>({
    queryKey: ['my-applications', id],
    queryFn: async () => {
      const { data } = await api.get(`/my-applications/${id}/`)
      return data
    },
    enabled: !!id,
  })
}

export function useSubmitApplication() {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, CreateApplicationData>({
    mutationFn: async (payload) => {
      const { data } = await api.post('/my-applications/', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
    },
  })
}

export function useSubmitForReview(id: string) {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/my-applications/${id}/submit/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
    },
  })
}

export function useAdminApplications(filters?: ApplicationFilters) {
  return useQuery<PaginatedResponse<ApplicationListItem>>({
    queryKey: ['admin-applications', filters],
    queryFn: async () => {
      const { data } = await api.get('/admin/applications/', { params: filters })
      return data
    },
  })
}

export function useAdminApplication(id: string) {
  return useQuery<Application>({
    queryKey: ['admin-applications', id],
    queryFn: async () => {
      const { data } = await api.get(`/admin/applications/${id}/`)
      return data
    },
    enabled: !!id,
  })
}

export function useStartReview(id: string) {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/admin/applications/${id}/start_review/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-applications'] })
    },
  })
}

export function useReviewAction(id: string) {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, ReviewActionData>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`/admin/applications/${id}/review_action/`, payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-applications'] })
    },
  })
}

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ['admin-dashboard'],
    queryFn: async () => {
      const { data } = await api.get('/admin/applications/dashboard/')
      return data
    },
  })
}
