'use client'

import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import { useAuth } from '@/hooks/useAuth'
import { useMyApplications } from '@/hooks/useApplications'
import { format } from 'date-fns'
import type { ApplicationStatus } from '@/types'

const statuses: ApplicationStatus[] = ['SUBMITTED', 'APPROVED', 'ENROLLED', 'CERTIFIED']
const statLabel: Partial<Record<ApplicationStatus, string>> = {
  SUBMITTED: 'Submitted',
  APPROVED: 'Approved',
  ENROLLED: 'Enrolled',
  CERTIFIED: 'Certified',
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { data, isLoading } = useMyApplications()
  const applications = data?.results ?? []

  const countByStatus = (status: ApplicationStatus) =>
    applications.filter((a) => a.status === status).length

  return (
    <StudentLayout>
      <PageHeader
        title={`Welcome back, ${user?.full_name?.split(' ')[0] ?? 'there'}`}
        subtitle="Here's an overview of your training activity."
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-8">
        {statuses.map((s) => (
          <Card key={s} className="text-center">
            <p className="text-3xl font-bold text-primary">{countByStatus(s)}</p>
            <p className="mt-1 text-xs text-gray-500">{statLabel[s]}</p>
          </Card>
        ))}
      </div>

      {/* Recent applications */}
      <Card header={<h2 className="text-base font-semibold text-gray-900">Recent Applications</h2>}>
        {isLoading && (
          <div className="flex justify-center py-8">
            <Spinner className="text-primary" />
          </div>
        )}
        {!isLoading && applications.length === 0 && (
          <p className="py-6 text-center text-sm text-gray-500">
            No applications yet.{' '}
            <a href="/courses" className="text-primary hover:underline">Browse courses</a> to get started.
          </p>
        )}
        {!isLoading && applications.length > 0 && (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="pb-2 font-medium">Course</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium hidden sm:table-cell">Submitted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {applications.slice(0, 8).map((app) => (
                <tr key={app.id}>
                  <td className="py-2.5 font-medium text-gray-800">{app.course_name}</td>
                  <td className="py-2.5"><Badge status={app.status} /></td>
                  <td className="py-2.5 text-gray-500 hidden sm:table-cell">
                    {app.submitted_at ? format(new Date(app.submitted_at), 'dd MMM yyyy') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </StudentLayout>
  )
}
