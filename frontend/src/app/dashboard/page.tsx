'use client'

import { useQuery } from '@tanstack/react-query'
import { Award } from 'lucide-react'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import { useAuth } from '@/hooks/useAuth'
import { useMyApplications } from '@/hooks/useApplications'
import { useMyCertificates } from '@/hooks/useCertificates'
import api from '@/lib/api'
import { format } from 'date-fns'
import type { ApplicationStatus, User, StudentEnrollment } from '@/types'

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

  const { data: me } = useQuery<User>({
    queryKey: ['me'],
    queryFn: () => api.get<User>('/users/me/').then(r => r.data),
  })

  const { data: enrollments = [] } = useQuery<StudentEnrollment[]>({
    queryKey: ['enrollments'],
    queryFn: () => api.get<StudentEnrollment[]>('/enrollments/').then(r => r.data),
  })

  const { data: certData } = useMyCertificates()
  const certificates = certData?.results ?? []

  const countByStatus = (status: ApplicationStatus) =>
    applications.filter((a) => a.status === status).length

  const activeEnrollments = enrollments.filter(e => e.status !== 'UNENROLLED')

  return (
    <StudentLayout>
      <PageHeader
        title={`Welcome back, ${user?.full_name?.split(' ')[0] ?? 'there'}`}
        subtitle="Here's an overview of your training activity."
      />

      {/* Student ID card — only shown once enrolled */}
      {me?.student_id && (
        <div className="bg-gradient-to-r from-green-700 to-green-900 rounded-xl p-5 mb-6 text-white flex items-center justify-between">
          <div>
            <p className="text-green-200 text-xs font-medium uppercase tracking-wider mb-1">
              Student ID
            </p>
            <p className="text-2xl font-bold tracking-widest font-mono">
              {me.student_id}
            </p>
            {me.zntc_email && (
              <p className="text-green-200 text-sm mt-1">{me.zntc_email}</p>
            )}
          </div>
          <div className="text-right">
            <p className="text-green-200 text-xs mb-2">Learning Portal</p>
            {process.env.NEXT_PUBLIC_MOODLE_URL ? (
              <a
                href={process.env.NEXT_PUBLIC_MOODLE_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-white text-green-800 font-semibold text-sm px-4 py-2 rounded-lg hover:bg-green-50 transition-colors"
              >
                Go to Moodle →
              </a>
            ) : (
              <span className="text-xs text-green-200">Moodle not configured</span>
            )}
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-8">
        {statuses.map((s) => (
          <Card key={s} className="text-center">
            <p className="text-3xl font-bold text-primary">{countByStatus(s)}</p>
            <p className="mt-1 text-xs text-gray-500">{statLabel[s]}</p>
          </Card>
        ))}
      </div>

      {/* My Courses — only shown when there are active enrollments */}
      {activeEnrollments.length > 0 && (
        <div className="mt-6 mb-6">
          <h2 className="text-base font-semibold text-gray-700 mb-3">My Courses</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {activeEnrollments.map(enrollment => {
              const canOpen = enrollment.status === 'ENROLLED' && !!enrollment.moodle_course_url
              const row = (
                <>
                  <div>
                    <p className="font-medium text-gray-800 text-sm">
                      {enrollment.course_name || 'Enrolled Course'}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Enrolled {enrollment.enrolled_at
                        ? new Date(enrollment.enrolled_at).toLocaleDateString('en-GB')
                        : '—'}
                    </p>
                  </div>
                  {canOpen && (
                    <span className="text-green-600 group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  )}
                  {enrollment.status === 'PENDING' || enrollment.status === 'ENROLLING' ? (
                    <span className="flex-shrink-0 text-xs text-amber-600">Setting up access…</span>
                  ) : null}
                  {enrollment.status === 'FAILED' && (
                    <span className="flex-shrink-0 text-xs text-red-500 text-right max-w-32">
                      Setup issue — contact training@zntc.ac.zw
                    </span>
                  )}
                </>
              )

              if (canOpen) {
                return (
                  <a
                    key={enrollment.id}
                    href={enrollment.moodle_course_url!}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-green-500 hover:shadow-sm transition-all group"
                  >
                    {row}
                  </a>
                )
              }

              return (
                <div
                  key={enrollment.id}
                  className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200"
                >
                  {row}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* My Certificates */}
      {certificates.length > 0 && (
        <div className="mb-6">
          <h2 className="text-base font-semibold text-gray-700 mb-3">My Certificates</h2>
          <div className="space-y-3">
            {certificates.map((cert) => (
              <div
                key={cert.id}
                className="flex items-center gap-4 p-4 bg-white rounded-lg border border-gray-200 hover:border-green-500 transition-colors"
              >
                <div className="w-10 h-10 bg-green-700 rounded-lg flex items-center justify-center flex-shrink-0 text-white">
                  <Award className="h-5 w-5" />
                </div>

                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800 text-sm truncate">
                    {cert.course_detail.fullname}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Issued {format(new Date(cert.issued_at), 'dd MMM yyyy')}
                  </p>
                  <p className="text-xs text-green-700 font-mono mt-0.5">
                    {cert.certificate_number}
                  </p>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  {cert.pdf_url ? (
                    <a
                      href={cert.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium bg-green-700 text-white px-3 py-1.5 rounded-lg hover:bg-green-800"
                    >
                      Download PDF
                    </a>
                  ) : (
                    <span className="text-xs text-gray-400">PDF generating…</span>
                  )}
                  <a
                    href={`/verify/${cert.certificate_number}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-green-700 hover:text-green-900 underline underline-offset-2"
                  >
                    Verify
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
