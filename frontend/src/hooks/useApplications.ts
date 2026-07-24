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

export function useUpdatePhoto(id: string) {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, File>({
    mutationFn: async (photo) => {
      const form = new FormData()
      form.append('student_photo', photo)
      const { data } = await api.patch(`/my-applications/${id}/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
    },
  })
}

export interface EditableApplicationFields {
  motivation: string
  is_resident: boolean
  hostel_name: string
  room_number: string
  guardian_name: string
  guardian_contact: string
  guardian_email: string
  responsible_party: string
}

export function useUpdateApplication(id: string) {
  const queryClient = useQueryClient()
  return useMutation<Application, Error, Partial<EditableApplicationFields>>({
    mutationFn: async (payload) => {
      const { data } = await api.patch(`/my-applications/${id}/`, payload)
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

interface DeEnrolPayload {
  type: 'MANDATORY' | 'VOLUNTARY'
  reason: string
}

// De-enrolment is processed asynchronously (queued as a Celery task that
// unenrols from Moodle before flipping the application status), so the
// status won't have changed yet when this resolves. Re-invalidate a couple
// of times shortly after to pick up the eventual DE_ENROLLED transition
// without a persistent poll.
function invalidateApplicationSoon(queryClient: ReturnType<typeof useQueryClient>, keys: string[][]) {
  const invalidate = () => keys.forEach((key) => queryClient.invalidateQueries({ queryKey: key }))
  invalidate()
  ;[2000, 5000, 10000].forEach((delay) => setTimeout(invalidate, delay))
}

export function useDeEnrolStudent(id: string) {
  const queryClient = useQueryClient()
  return useMutation<{ status: string }, Error, DeEnrolPayload>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`/admin/applications/${id}/de-enrol/`, payload)
      return data
    },
    onSuccess: () => {
      invalidateApplicationSoon(queryClient, [['admin-applications'], ['admin-applications', id]])
    },
  })
}

export function useRequestWithdrawal(id: string) {
  const queryClient = useQueryClient()
  return useMutation<{ status: string }, Error, { reason: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post(`/my-applications/${id}/request-withdrawal/`, payload)
      return data
    },
    onSuccess: () => {
      invalidateApplicationSoon(queryClient, [['my-applications'], ['my-applications', id]])
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
