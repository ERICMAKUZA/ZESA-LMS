'use client'

import { ArrowLeft, CheckCircle, Clock } from 'lucide-react'
import Link from 'next/link'
import { format } from 'date-fns'
import StudentLayout from '@/components/layout/StudentLayout'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useApplication, useSubmitForReview } from '@/hooks/useApplications'
import { useToast } from '@/components/ui/Toast'
import type { ApplicationStatus } from '@/types'

const timelineStatuses: ApplicationStatus[] = [
  'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'PAYMENT_PENDING', 'PAYMENT_CONFIRMED', 'ENROLLED', 'CERTIFIED',
]

export default function ApplicationDetailPage({ params }: { params: { id: string } }) {
  const { data: app, isLoading } = useApplication(params.id)
  const submitMutation = useSubmitForReview(params.id)
  const { toast } = useToast()

  const handleSubmit = async () => {
    try {
      await submitMutation.mutateAsync()
      toast({ variant: 'success', title: 'Application submitted', description: 'A reviewer will be in touch soon.' })
    } catch {
      toast({ variant: 'error', title: 'Submission failed', description: 'Please try again.' })
    }
  }

  if (isLoading) {
    return (
      <StudentLayout>
        <div className="flex justify-center py-16"><Spinner size="lg" className="text-primary" /></div>
      </StudentLayout>
    )
  }

  if (!app) {
    return (
      <StudentLayout>
        <p className="text-center text-sm text-gray-500 py-10">Application not found.</p>
      </StudentLayout>
    )
  }

  const currentIdx = timelineStatuses.indexOf(app.status as ApplicationStatus)

  return (
    <StudentLayout>
      <div className="mb-4">
        <Link href="/applications" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary">
          <ArrowLeft className="h-4 w-4" /> Back to applications
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Header card */}
          <Card>
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{app.course_name}</h1>
                <p className="mt-1 text-sm text-gray-500">Submitted {app.submitted_at ? format(new Date(app.submitted_at), 'dd MMM yyyy') : 'not yet'}</p>
              </div>
              <Badge status={app.status} />
            </div>
            {app.rejection_reason && (
              <div className="mt-4 rounded-md bg-red-50 border border-red-200 p-3">
                <p className="text-sm font-medium text-red-700">Rejection reason</p>
                <p className="text-sm text-red-600 mt-1">{app.rejection_reason}</p>
              </div>
            )}
            {app.more_info_request && app.status === 'MORE_INFO_REQUESTED' && (
              <div className="mt-4 rounded-md bg-orange-50 border border-orange-200 p-3">
                <p className="text-sm font-medium text-orange-700">Additional information requested</p>
                <p className="text-sm text-orange-600 mt-1">{app.more_info_request}</p>
              </div>
            )}
            {app.reviewer_notes && (
              <div className="mt-4 rounded-md bg-blue-50 border border-blue-200 p-3">
                <p className="text-sm font-medium text-blue-700">Reviewer notes</p>
                <p className="text-sm text-blue-600 mt-1">{app.reviewer_notes}</p>
              </div>
            )}
            {(app.status === 'DRAFT' || app.status === 'MORE_INFO_REQUESTED') && (
              <div className="mt-4">
                <Button onClick={handleSubmit} loading={submitMutation.isPending}>
                  {app.status === 'MORE_INFO_REQUESTED' ? 'Resubmit Application' : 'Submit Application'}
                </Button>
              </div>
            )}
          </Card>

          {/* Status timeline */}
          <Card header={<h2 className="font-semibold text-gray-900">Progress</h2>}>
            <ol className="relative ml-3 border-l border-gray-200">
              {timelineStatuses.map((s, i) => {
                const past = i <= currentIdx
                const current = i === currentIdx
                const entry = app.recent_history.find((h) => h.to_status === s)
                return (
                  <li key={s} className="mb-6 ml-5 last:mb-0">
                    <span className={`absolute -left-2.5 flex h-5 w-5 items-center justify-center rounded-full ${past ? 'bg-primary' : 'bg-gray-200'}`}>
                      {past && <CheckCircle className="h-3.5 w-3.5 text-white" />}
                      {!past && <Clock className="h-3.5 w-3.5 text-gray-400" />}
                    </span>
                    <p className={`text-sm font-medium ${current ? 'text-primary' : past ? 'text-gray-700' : 'text-gray-400'}`}>
                      <Badge status={s} />
                    </p>
                    {entry && (
                      <p className="mt-0.5 text-xs text-gray-400">
                        {format(new Date(entry.changed_at), 'dd MMM yyyy HH:mm')}
                        {entry.changed_by_name !== 'System' && ` · ${entry.changed_by_name}`}
                      </p>
                    )}
                  </li>
                )
              })}
            </ol>
          </Card>
        </div>

        {/* Details sidebar */}
        <div className="flex flex-col gap-4">
          <Card header={<h2 className="font-semibold text-gray-900">Application Details</h2>}>
            <dl className="flex flex-col gap-3 text-sm">
              <div><dt className="text-xs text-gray-500">Department</dt><dd className="text-gray-800">{app.department || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Employee ID</dt><dd className="text-gray-800">{app.employee_id || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Line Manager</dt><dd className="text-gray-800">{app.line_manager_email || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Motivation</dt><dd className="text-gray-800 whitespace-pre-line">{app.motivation}</dd></div>
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
    </StudentLayout>
  )
}
