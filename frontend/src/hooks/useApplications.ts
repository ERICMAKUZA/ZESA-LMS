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
  escalated?: boolean
}

type CreateApplicationPayload = FormData | Record<string, unknown>

interface ReviewActionData {
  action: 'approve' | 'reject' | 'request_more_info'
  notes?: string
  rejection_reason?: string
  assigned_centre?: string
}

interface ConfirmPaymentData {
  method: 'CASH' | 'EFT' | 'RTGS' | 'ECOCASH' | 'ZIMSWITCH' | 'COMPANY'
  reference: string
  amount: number
}

interface ConfirmPaymentResponse {
  application_status: string
  payment_status: string
  payment_id: string
  message: string
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
  return useMutation<Application, Error, CreateApplicationPayload>({
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
    // Poll while Moodle enrolment is in flight after a payment confirmation,
    // so the sync banner/badge updates without a manual reload. Stops as
    // soon as the enrolment reaches a terminal state.
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.status !== 'PAYMENT_CONFIRMED') return false
      const syncing = !data.enrollment || ['PENDING', 'ENROLLING'].includes(data.enrollment.status)
      return syncing ? 5000 : false
    },
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

export function useIssueCertificate(id: string) {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post(`/admin/applications/${id}/issue_certificate/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-applications'] })
    },
  })
}

export function useConfirmPayment(id: string) {
  const queryClient = useQueryClient()
  return useMutation<ConfirmPaymentResponse, Error, ConfirmPaymentData>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`/payments/applications/${id}/confirm-manual/`, payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-applications'] })
    },
  })
}

export function useRetryMoodleSync(applicationId: string) {
  const queryClient = useQueryClient()
  return useMutation<unknown, Error, string>({
    mutationFn: async (enrollmentId) => {
      const { data } = await api.post(`/admin/enrollments/${enrollmentId}/retry/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-applications', applicationId] })
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
