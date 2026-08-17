'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Notification, PaginatedResponse } from '@/types'

export function useNotifications() {
  return useQuery<PaginatedResponse<Notification>>({
    queryKey: ['notifications'],
    queryFn: async () => {
      const { data } = await api.get('/notifications/')
      return data
    },
    refetchInterval: 30_000,
  })
}

export function useUnreadNotificationCount() {
  return useQuery<{ count: number }>({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () => {
      const { data } = await api.get('/notifications/unread-count/')
      return data
    },
    refetchInterval: 30_000,
  })
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/notifications/${id}/mark-read/`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/notifications/mark-all-read/')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}
