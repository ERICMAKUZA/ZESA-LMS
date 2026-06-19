'use client'

import { useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Spinner from '@/components/ui/Spinner'
import { useAdminApplications } from '@/hooks/useApplications'
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

  const { data, isLoading } = useAdminApplications({
    status: status || undefined,
    applicant__email: email || undefined,
    submitted_after: submittedAfter || undefined,
    submitted_before: submittedBefore || undefined,
  })

  const applications = data?.results ?? []

  return (
    <AdminLayout>
      <PageHeader title="Applications" subtitle={`${data?.count ?? 0} total`} />

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
                      <p className="font-medium text-gray-900">{app.applicant_name}</p>
                      <p className="text-xs text-gray-500">{app.applicant_email}</p>
                    </td>
                    <td className="py-3 text-gray-700">{app.course_name}</td>
                    <td className="py-3"><Badge status={app.status as ApplicationStatus} /></td>
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
    </AdminLayout>
  )
}
