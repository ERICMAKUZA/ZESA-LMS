'use client'

import Link from 'next/link'
import { format } from 'date-fns'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useMyApplications } from '@/hooks/useApplications'

export default function ApplicationsPage() {
  const { data, isLoading } = useMyApplications()
  const applications = data?.results ?? []

  return (
    <StudentLayout>
      <PageHeader
        title="My Applications"
        subtitle="Track all your training applications."
        action={
          <Link href="/courses">
            <Button variant="outline" size="sm">Browse Courses</Button>
          </Link>
        }
      />

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && applications.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">
            You haven&apos;t applied for any courses yet.
          </p>
        )}

        {!isLoading && applications.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                  <th className="pb-3 text-left font-medium">Course</th>
                  <th className="pb-3 text-left font-medium">Status</th>
                  <th className="pb-3 text-left font-medium hidden sm:table-cell">Submitted</th>
                  <th className="pb-3 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {applications.map((app) => (
                  <tr key={app.id}>
                    <td className="py-3">
                      <Link href={`/applications/${app.id}`} className="font-medium text-gray-900 hover:text-primary">
                        {app.course_name}
                      </Link>
                    </td>
                    <td className="py-3"><Badge status={app.status} /></td>
                    <td className="py-3 text-gray-500 hidden sm:table-cell">
                      {app.submitted_at ? format(new Date(app.submitted_at), 'dd MMM yyyy') : '—'}
                    </td>
                    <td className="py-3 text-right">
                      {app.status === 'DRAFT' && (
                        <Link href={`/applications/${app.id}`}>
                          <Button size="sm">Submit</Button>
                        </Link>
                      )}
                      {app.status === 'MORE_INFO_REQUESTED' && (
                        <Link href={`/applications/${app.id}`}>
                          <Button size="sm" variant="secondary">Respond</Button>
                        </Link>
                      )}
                      {app.status === 'APPROVED' && (
                        <Link href={`/applications/${app.id}`}>
                          <Button size="sm" variant="secondary">Pay Now</Button>
                        </Link>
                      )}
                      {!['DRAFT', 'MORE_INFO_REQUESTED', 'APPROVED'].includes(app.status) && (
                        <Link href={`/applications/${app.id}`} className="text-xs text-primary hover:underline">
                          View
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </StudentLayout>
  )
}
