'use client'

import { useState } from 'react'
import { ArrowLeft, CheckCircle, Clock } from 'lucide-react'
import Link from 'next/link'
import { format } from 'date-fns'
import AdminLayout from '@/components/layout/AdminLayout'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useAdminApplication, useStartReview, useReviewAction } from '@/hooks/useApplications'
import type { ApplicationStatus } from '@/types'

type ReviewAction = 'approve' | 'reject' | 'request_more_info'

const actionLabels: Record<ReviewAction, string> = {
  approve: 'Approve Application',
  reject: 'Reject Application',
  request_more_info: 'Request More Info',
}

const timelineStatuses: ApplicationStatus[] = [
  'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'PAYMENT_PENDING', 'PAYMENT_CONFIRMED', 'ENROLLED', 'CERTIFIED',
]

export default function AdminApplicationDetailPage({ params }: { params: { id: string } }) {
  const { data: app, isLoading } = useAdminApplication(params.id)
  const startReview = useStartReview(params.id)
  const reviewAction = useReviewAction(params.id)
  const { toast } = useToast()

  const [modalAction, setModalAction] = useState<ReviewAction | null>(null)
  const [notes, setNotes] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')

  const handleStartReview = async () => {
    try {
      await startReview.mutateAsync()
      toast({ variant: 'success', title: 'Review started' })
    } catch {
      toast({ variant: 'error', title: 'Failed to start review' })
    }
  }

  const handleReviewAction = async () => {
    if (!modalAction) return
    try {
      await reviewAction.mutateAsync({
        action: modalAction,
        notes: notes || undefined,
        rejection_reason: rejectionReason || undefined,
      })
      toast({ variant: 'success', title: actionLabels[modalAction] + ' successful' })
      setModalAction(null)
      setNotes('')
      setRejectionReason('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ variant: 'error', title: 'Action failed', description: msg })
    }
  }

  if (isLoading) {
    return <AdminLayout><div className="flex justify-center py-16"><Spinner size="lg" className="text-primary" /></div></AdminLayout>
  }

  if (!app) {
    return <AdminLayout><p className="text-center text-sm text-gray-500 py-10">Application not found.</p></AdminLayout>
  }

  const currentIdx = timelineStatuses.indexOf(app.status as ApplicationStatus)

  return (
    <AdminLayout>
      <div className="mb-4">
        <Link href="/admin/applications" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary">
          <ArrowLeft className="h-4 w-4" /> Back to applications
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Header */}
          <Card>
            <div className="flex items-start justify-between flex-wrap gap-3">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{app.course_name}</h1>
                <p className="mt-1 text-sm text-gray-500">
                  {app.applicant_name} · {app.applicant_email}
                </p>
              </div>
              <Badge status={app.status} />
            </div>

            {/* Action buttons */}
            <div className="mt-5 flex flex-wrap gap-2">
              {app.status === 'SUBMITTED' && (
                <Button onClick={handleStartReview} loading={startReview.isPending} size="sm">
                  Start Review
                </Button>
              )}
              {app.status === 'UNDER_REVIEW' && (
                <>
                  <Button size="sm" onClick={() => setModalAction('approve')}>Approve</Button>
                  <Button size="sm" variant="danger" onClick={() => setModalAction('reject')}>Reject</Button>
                  <Button size="sm" variant="outline" onClick={() => setModalAction('request_more_info')}>Request Info</Button>
                </>
              )}
            </div>
          </Card>

          {/* Status history */}
          <Card header={<h2 className="font-semibold text-gray-900">Status History</h2>}>
            {app.recent_history.length === 0 && (
              <p className="text-sm text-gray-500">No status changes recorded.</p>
            )}
            <ol className="relative ml-3 border-l border-gray-200">
              {app.recent_history.map((entry) => (
                <li key={entry.id} className="mb-5 ml-5 last:mb-0">
                  <span className="absolute -left-2.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                    <CheckCircle className="h-3.5 w-3.5 text-white" />
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge status={entry.from_status} />
                    <span className="text-gray-400">→</span>
                    <Badge status={entry.to_status} />
                  </div>
                  <p className="mt-0.5 text-xs text-gray-400">
                    {format(new Date(entry.changed_at), 'dd MMM yyyy HH:mm')} · {entry.changed_by_name}
                  </p>
                  {entry.notes && <p className="mt-1 text-sm text-gray-600">{entry.notes}</p>}
                </li>
              ))}
            </ol>
          </Card>

          {/* Timeline progress */}
          <Card header={<h2 className="font-semibold text-gray-900">Pipeline Stage</h2>}>
            <ol className="relative ml-3 border-l border-gray-200">
              {timelineStatuses.map((s, i) => {
                const past = i <= currentIdx
                return (
                  <li key={s} className="mb-5 ml-5 last:mb-0">
                    <span className={`absolute -left-2.5 flex h-5 w-5 items-center justify-center rounded-full ${past ? 'bg-primary' : 'bg-gray-200'}`}>
                      {past ? <CheckCircle className="h-3.5 w-3.5 text-white" /> : <Clock className="h-3.5 w-3.5 text-gray-400" />}
                    </span>
                    <Badge status={s} />
                  </li>
                )
              })}
            </ol>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="flex flex-col gap-4">
          <Card header={<h2 className="font-semibold text-gray-900">Applicant Info</h2>}>
            <dl className="flex flex-col gap-3 text-sm">
              <div><dt className="text-xs text-gray-500">Department</dt><dd>{app.department || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Employee ID</dt><dd>{app.employee_id || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Line Manager</dt><dd>{app.line_manager_email}</dd></div>
              <div><dt className="text-xs text-gray-500">Reviewer</dt><dd>{app.reviewer_name ?? 'Unassigned'}</dd></div>
              <div><dt className="text-xs text-gray-500">Motivation</dt><dd className="whitespace-pre-line">{app.motivation}</dd></div>
            </dl>
          </Card>

          {app.documents.length > 0 && (
            <Card header={<h2 className="font-semibold text-gray-900">Documents</h2>}>
              <ul className="flex flex-col gap-2">
                {app.documents.map((doc) => (
                  <li key={doc.id}>
                    <a href={doc.file} className="text-sm text-primary hover:underline" target="_blank" rel="noreferrer">
                      {doc.filename}
                    </a>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      </div>

      {/* Review action modal */}
      <Modal
        open={!!modalAction}
        onOpenChange={(open) => { if (!open) setModalAction(null) }}
        title={modalAction ? actionLabels[modalAction] : ''}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalAction(null)}>Cancel</Button>
            <Button
              variant={modalAction === 'reject' ? 'danger' : 'primary'}
              loading={reviewAction.isPending}
              onClick={handleReviewAction}
            >
              Confirm
            </Button>
          </>
        }
      >
        {modalAction === 'reject' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Rejection reason <span className="text-danger">*</span></label>
            <textarea
              rows={3}
              className="block w-full rounded-md border-gray-300 text-sm focus:border-primary focus:ring-primary"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Explain why this application is being rejected…"
            />
          </div>
        )}
        {(modalAction === 'approve' || modalAction === 'request_more_info') && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes {modalAction === 'request_more_info' && <span className="text-danger">*</span>}
            </label>
            <textarea
              rows={3}
              className="block w-full rounded-md border-gray-300 text-sm focus:border-primary focus:ring-primary"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={modalAction === 'request_more_info' ? 'What information is needed from the applicant?' : 'Optional reviewer notes…'}
            />
          </div>
        )}
        <p className="text-sm text-gray-600">
          {modalAction === 'approve' && 'The applicant will be notified and prompted to complete payment.'}
          {modalAction === 'reject' && 'The applicant will be notified with the reason provided.'}
          {modalAction === 'request_more_info' && 'The applicant will be asked to provide additional information and resubmit.'}
        </p>
      </Modal>
    </AdminLayout>
  )
}
