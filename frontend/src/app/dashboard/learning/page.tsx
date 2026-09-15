'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, CalendarDays, CheckCircle2, Clock3 } from 'lucide-react'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'
import type { StudentEnrollment } from '@/types'

type AttendanceOutcome = {
  response: 'CONFIRMED' | 'DEFERRED' | 'PENDING_STAFF'
  responded_at: string
  target_schedule: string | null
  audit_note: string
}

type LearningEnrollment = StudentEnrollment & {
  attendance_response: AttendanceOutcome | null
}

function displayDate(value: string | null) {
  if (!value) return 'To be confirmed'
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

export default function LearningPage() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [confirmingDeferral, setConfirmingDeferral] = useState<string | null>(null)
  const { data: enrollments = [], isLoading, isError, refetch } = useQuery<LearningEnrollment[]>({
    queryKey: ['enrollments'],
    queryFn: () => api.get<LearningEnrollment[]>('/enrollments/').then(r => r.data),
  })
  const respond = useMutation({
    mutationFn: ({ id, response }: { id: string; response: 'CONFIRMED' | 'DEFER' }) =>
      api.post<AttendanceOutcome>(`/enrollments/${id}/attendance-response/`, { response })
        .then(r => r.data),
    onSuccess: (outcome) => {
      setConfirmingDeferral(null)
      queryClient.invalidateQueries({ queryKey: ['enrollments'] })
      toast({
        variant: 'success',
        title: outcome.response === 'CONFIRMED' ? 'Attendance confirmed' : 'Deferral request recorded',
        description: outcome.response === 'PENDING_STAFF'
          ? 'No later intake has space right now. Training staff will review your request.'
          : outcome.response === 'DEFERRED'
            ? 'Your new intake is shown on this page.'
            : undefined,
      })
    },
    onError: () => toast({
      variant: 'error', title: 'Could not save your response',
      description: 'Please refresh the page and try again.',
    }),
  })

  return (
    <StudentLayout>
      <PageHeader
        title="My Learning"
        subtitle="Review your upcoming training and confirm whether you can attend."
      />

      <div className="mb-6 rounded-xl border border-green-200 bg-gradient-to-r from-green-50 to-white p-5">
        <p className="text-sm font-semibold text-green-900">Your place, your response</p>
        <p className="mt-1 text-sm text-green-800">
          Confirm your attendance for the scheduled intake, or request a later one.
          If no later intake has space, your request will go to training staff for review.
        </p>
      </div>

      {isLoading && <div className="flex justify-center py-12"><Spinner className="text-primary" /></div>}
      {isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
          We could not load your learning records.{' '}
          <button type="button" onClick={() => refetch()} className="font-semibold underline">Try again</button>
        </div>
      )}
      {!isLoading && !isError && enrollments.filter(e => e.status !== 'UNENROLLED').length === 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-gray-600">
          <BookOpen className="mx-auto mb-3 h-8 w-8 text-green-700" />
          <p className="font-semibold text-gray-900">No active learning records yet</p>
          <p className="mt-1 text-sm">Your courses will appear here after enrollment.</p>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {enrollments.filter(e => e.status !== 'UNENROLLED').map(enrollment => {
          const outcome = enrollment.attendance_response
          const pending = respond.isPending && respond.variables?.id === enrollment.id
          return (
            <article key={enrollment.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-green-100 p-2.5 text-green-800">
                  <BookOpen className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <h2 className="font-semibold text-gray-900">{enrollment.course_name}</h2>
                  <p className="mt-1 flex items-center gap-1.5 text-sm text-gray-600">
                    <CalendarDays className="h-4 w-4 shrink-0" />
                    Starts {displayDate(enrollment.start_date)}
                  </p>
                  {enrollment.end_date && (
                    <p className="mt-1 text-xs text-gray-500">Ends {displayDate(enrollment.end_date)}</p>
                  )}
                </div>
              </div>

              {outcome ? (
                <div className={`mt-5 rounded-lg p-3 text-sm ${outcome.response === 'PENDING_STAFF'
                  ? 'bg-amber-50 text-amber-900' : 'bg-green-50 text-green-900'}`}>
                  <div className="flex items-center gap-2 font-semibold">
                    {outcome.response === 'PENDING_STAFF'
                      ? <Clock3 className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                    {outcome.response === 'CONFIRMED' ? 'Attendance confirmed'
                      : outcome.response === 'DEFERRED' ? 'Moved to a later intake'
                        : 'Deferral awaiting staff review'}
                  </div>
                  {outcome.response === 'PENDING_STAFF' && (
                    <p className="mt-1">Your current intake remains unchanged until staff arrange a place.</p>
                  )}
                </div>
              ) : enrollment.is_suspended ? (
                <p className="mt-5 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                  Attendance responses are unavailable while this enrollment is suspended.
                </p>
              ) : confirmingDeferral === enrollment.id ? (
                <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <p className="text-sm text-amber-950">
                    Request a later intake? If one has space, your enrollment will move immediately.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button" disabled={pending}
                      onClick={() => respond.mutate({ id: enrollment.id, response: 'DEFER' })}
                      className="rounded-lg bg-amber-700 px-3 py-2 text-sm font-semibold text-white hover:bg-amber-800 disabled:opacity-50"
                    >
                      {pending ? 'Submitting…' : 'Request deferral'}
                    </button>
                    <button
                      type="button" disabled={pending} onClick={() => setConfirmingDeferral(null)}
                      className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-white"
                    >Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="mt-5 flex flex-wrap gap-2 border-t border-gray-100 pt-4">
                  <button
                    type="button" disabled={respond.isPending}
                    onClick={() => respond.mutate({ id: enrollment.id, response: 'CONFIRMED' })}
                    className="rounded-lg bg-green-700 px-3 py-2 text-sm font-semibold text-white hover:bg-green-800 disabled:opacity-50"
                  >
                    {pending ? 'Saving…' : 'Confirm attendance'}
                  </button>
                  <button
                    type="button" disabled={respond.isPending}
                    onClick={() => setConfirmingDeferral(enrollment.id)}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >Defer</button>
                </div>
              )}
            </article>
          )
        })}
      </div>
    </StudentLayout>
  )
}
