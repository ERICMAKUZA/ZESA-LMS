'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import AdminLayout from '@/components/layout/AdminLayout'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/hooks/useAuth'
import { useAdminEnrollments, useRetryEnrollment } from '@/hooks/useEnrollments'
import api from '@/lib/api'

const MOODLE_STATUS: Record<string, { label: string; className: string }> = {
  ENROLLED:   { label: '✓ Moodle',    className: 'bg-green-100 text-green-700' },
  FAILED:     { label: '✗ Failed',    className: 'bg-red-100 text-red-700' },
  ENROLLING:  { label: 'Syncing…',    className: 'bg-amber-100 text-amber-700' },
  PENDING:    { label: 'Syncing…',    className: 'bg-amber-100 text-amber-700' },
  UNENROLLED: { label: 'Unenrolled',  className: 'bg-gray-100 text-gray-600' },
}

const HEXCO_LABEL: Record<string, string> = {
  NC: 'NC',
  ND: 'ND',
}

export default function AdminEnrolmentsPage() {
  const { user } = useAuth()
  const [search, setSearch] = useState('')
  const [exporting, setExporting] = useState(false)
  const { data, isLoading } = useAdminEnrollments({ search: search || undefined })
  const retryEnrollment = useRetryEnrollment()
  const { toast } = useToast()

  const enrolments = data?.results ?? []

  const handleRetry = async (enrollmentId: string) => {
    try {
      await retryEnrollment.mutateAsync(enrollmentId)
      toast({ variant: 'success', title: 'Moodle sync queued.' })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ variant: 'error', title: 'Failed to queue retry', description: msg })
    }
  }

  const handleExportCsv = async () => {
    setExporting(true)
    try {
      const response = await api.get('/admin/enrollments/export/', {
        responseType: 'blob',
        params: { search: search || undefined },
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `zntc_enrolled_students_${format(new Date(), 'yyyyMMdd_HHmm')}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast({ variant: 'error', title: 'Failed to export CSV' })
    } finally {
      setExporting(false)
    }
  }

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enrolled Students</h1>
          <p className="mt-1 text-sm text-gray-500">{data?.count ?? 0} total</p>
        </div>
        {user?.role === 'ADMIN' && (
          <Button variant="outline" onClick={handleExportCsv} loading={exporting}>
            Export CSV
          </Button>
        )}
      </div>

      <Card className="mb-6">
        <Input
          label="Search"
          placeholder="Search by name, student ID, or reference…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Card>

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && enrolments.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">No enrolled students match your search.</p>
        )}

        {!isLoading && enrolments.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                  <th className="pb-3 text-left font-medium">Student ID</th>
                  <th className="pb-3 text-left font-medium">Student</th>
                  <th className="pb-3 text-left font-medium">Course</th>
                  <th className="pb-3 text-left font-medium">Centre</th>
                  <th className="pb-3 text-left font-medium">Dept</th>
                  <th className="pb-3 text-left font-medium">Programme</th>
                  <th className="pb-3 text-left font-medium">Moodle</th>
                  <th className="pb-3 text-left font-medium">Enrolled</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {enrolments.map((e) => {
                  const moodle = MOODLE_STATUS[e.status] ?? { label: e.status, className: 'bg-gray-100 text-gray-600' }
                  return (
                    <tr key={e.id}>
                      <td className="py-3">
                        {e.student_id ? (
                          <span className="inline-flex items-center rounded-full bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-1">
                            {e.student_id}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-3">
                        <p className="font-medium text-gray-900">{e.applicant_name}</p>
                        <p className="text-xs text-gray-500">{e.zntc_email || e.applicant_email}</p>
                      </td>
                      <td className="py-3 text-gray-700">{e.course_name}</td>
                      <td className="py-3 text-gray-700">{e.assigned_centre_name || '—'}</td>
                      <td className="py-3 text-gray-700">{e.department || '—'}</td>
                      <td className="py-3 text-gray-700">{HEXCO_LABEL[e.hexco_level] || 'Short Course'}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-semibold rounded-full px-2.5 py-1 ${moodle.className}`}>
                            {moodle.label}
                          </span>
                          {e.status === 'FAILED' && (
                            <button
                              onClick={() => handleRetry(e.id)}
                              disabled={retryEnrollment.isPending}
                              className="text-xs font-medium text-primary hover:underline disabled:opacity-50"
                            >
                              Retry
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="py-3 text-gray-500">
                        {e.enrolled_at ? format(new Date(e.enrolled_at), 'dd MMM yyyy') : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </AdminLayout>
  )
}
