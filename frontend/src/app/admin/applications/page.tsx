'use client'

import { useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import AdminLayout from '@/components/layout/AdminLayout'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Spinner from '@/components/ui/Spinner'
import WalkInModal from '@/components/WalkInModal'
import { useAdminApplications, useDashboardStats } from '@/hooks/useApplications'
import type { ApplicationStatus } from '@/types'

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'SUBMITTED',           label: 'Submitted' },
  { value: 'UNDER_REVIEW',        label: 'Under Review' },
  { value: 'MORE_INFO_REQUESTED', label: 'More Info Requested' },
  { value: 'APPROVED',            label: 'Approved' },
  { value: 'REJECTED',            label: 'Rejected' },
  { value: 'PAYMENT_PENDING',     label: 'Payment Pending' },
  { value: 'PAYMENT_CONFIRMED',   label: 'Payment Confirmed' },
  { value: 'ENROLLED',            label: 'Enrolled' },
  { value: 'CERTIFIED',           label: 'Certified' },
]

export default function AdminApplicationsPage() {
  const [status, setStatus] = useState('')
  const [email, setEmail] = useState('')
  const [submittedAfter, setSubmittedAfter] = useState('')
  const [submittedBefore, setSubmittedBefore] = useState('')
  const [escalatedOnly, setEscalatedOnly] = useState(false)
  const [walkInOpen, setWalkInOpen] = useState(false)

  const { data, isLoading } = useAdminApplications({
    status: status || undefined,
    applicant__email: email || undefined,
    submitted_after: submittedAfter || undefined,
    submitted_before: submittedBefore || undefined,
    escalated: escalatedOnly || undefined,
  })
  const { data: stats } = useDashboardStats()

  const applications = data?.results ?? []
  const awaitingPaymentCount = stats?.approved_awaiting_payment ?? 0

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
          <p className="mt-1 text-sm text-gray-500">{data?.count ?? 0} total</p>
        </div>
        <Button variant="primary" onClick={() => setWalkInOpen(true)}>
          + Register Walk-in
        </Button>
      </div>

      {/* Quick filter */}
      {awaitingPaymentCount > 0 && (
        <button
          onClick={() => setStatus('PAYMENT_PENDING')}
          className={`mb-4 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
            status === 'PAYMENT_PENDING'
              ? 'bg-amber-600 text-white border-amber-600'
              : 'text-amber-700 border-amber-200 bg-amber-50 hover:bg-amber-100'
          }`}
        >
          Awaiting Payment ({awaitingPaymentCount})
        </button>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Select
            label="Status"
            options={STATUS_OPTIONS}
            value={status}
            onValueChange={setStatus}
          />
          <Input
            label="Applicant email"
            type="email"
            placeholder="Search by email…"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="Submitted after"
            type="date"
            value={submittedAfter}
            onChange={(e) => setSubmittedAfter(e.target.value)}
          />
          <Input
            label="Submitted before"
            type="date"
            value={submittedBefore}
            onChange={(e) => setSubmittedBefore(e.target.value)}
          />
        </div>
        <div className="mt-3 pt-3 border-t border-gray-100">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer w-fit">
            <input
              type="checkbox"
              checked={escalatedOnly}
              onChange={(e) => setEscalatedOnly(e.target.checked)}
              className="w-4 h-4 accent-red-600"
            />
            Show escalated only
          </label>
        </div>
      </Card>

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && applications.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">No applications match your filters.</p>
        )}

        {!isLoading && applications.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                  <th className="pb-3 text-left font-medium">Applicant</th>
                  <th className="pb-3 text-left font-medium">Course</th>
                  <th className="pb-3 text-left font-medium">Status</th>
                  <th className="pb-3 text-left font-medium hidden lg:table-cell">Submitted</th>
                  <th className="pb-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {applications.map((app) => (
                  <tr key={app.id}>
                    <td className="py-3">
                      <p className="font-medium text-gray-900 flex items-center gap-1.5">
                        {app.applicant_name}
                        {app.source === 'WALK_IN' && (
                          <span className="inline-block text-[10px] font-bold uppercase tracking-wider bg-orange-100 text-orange-700 border border-orange-300 rounded px-1.5 py-0.5">
                            Walk-in
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500">{app.applicant_email}</p>
                    </td>
                    <td className="py-3 text-gray-700">{app.course_name}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <Badge status={app.status as ApplicationStatus} />
                        {app.escalated && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider bg-red-100 text-red-700 border border-red-300 rounded px-1.5 py-0.5 animate-pulse">
                            ⚑ Escalated
                          </span>
                        )}
                        {app.enrollment_status === 'FAILED' && (
                          <span className="text-xs font-semibold bg-red-100 text-red-700 rounded-full px-2.5 py-1">
                            Moodle Sync Failed
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 text-gray-500 hidden lg:table-cell">
                      {app.submitted_at ? format(new Date(app.submitted_at), 'dd MMM yyyy') : '—'}
                    </td>
                    <td className="py-3 text-right">
                      <Link href={`/admin/applications/${app.id}`}>
                        <Button size="sm" variant="outline">Review</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <WalkInModal open={walkInOpen} onClose={() => setWalkInOpen(false)} />
    </AdminLayout>
  )
}
