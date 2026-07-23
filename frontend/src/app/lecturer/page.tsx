'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { CheckCircle2, AlertTriangle } from 'lucide-react'
import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import Modal from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { useLecturerApplications, useLecturerSignOff } from '@/hooks/useLecturer'
import type { LecturerApplication } from '@/types'

function SignOffModal({
  application,
  onOpenChange,
}: {
  application: LecturerApplication | null
  onOpenChange: (open: boolean) => void
}) {
  const [notes, setNotes] = useState('')
  const { toast } = useToast()
  const signOff = useLecturerSignOff(application?.id ?? '')

  const close = () => {
    onOpenChange(false)
    setNotes('')
  }

  const handleConfirm = async () => {
    try {
      const data = await signOff.mutateAsync({ notes })
      toast({
        variant: 'success',
        title: 'Sign-off complete',
        description: data.certificate_number
          ? `Certificate ${data.certificate_number} issued and emailed to the student.`
          : data.message,
      })
      close()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ variant: 'error', title: 'Sign-off failed', description: msg })
    }
  }

  if (!application) return null

  return (
    <Modal
      open={!!application}
      onOpenChange={(open) => { if (!open) close() }}
      title="Sign Off Completion"
      footer={
        <>
          <Button variant="ghost" onClick={close}>Cancel</Button>
          <Button variant="danger" loading={signOff.isPending} onClick={handleConfirm}>
            Confirm Sign-off &amp; Issue Certificate
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="rounded-lg bg-gray-50 p-4 text-sm">
          <p><span className="text-gray-500">Student:</span> <span className="font-medium text-gray-900">{application.applicant_name}</span></p>
          <p><span className="text-gray-500">Course:</span> <span className="font-medium text-gray-900">{application.course_name}</span></p>
          <p><span className="text-gray-500">Centre:</span> <span className="font-medium text-gray-900">{application.assigned_centre_name ?? '—'}</span></p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Performance notes / observations
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Optional"
          />
        </div>

        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>This will immediately issue the student&apos;s certificate. This cannot be undone.</p>
        </div>
      </div>
    </Modal>
  )
}

export default function LecturerDashboardPage() {
  const { data, isLoading } = useLecturerApplications()
  const [signOffTarget, setSignOffTarget] = useState<LecturerApplication | null>(null)
  const students = data?.results ?? []

  return (
    <AdminLayout>
      <PageHeader title="My Students" subtitle={`${data?.count ?? 0} students enrolled in your courses`} />

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && students.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">
            No enrolled students yet. Students will appear here once they&apos;re enrolled in a course you&apos;re assigned to.
          </p>
        )}

        {!isLoading && students.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                  <th className="pb-3 text-left font-medium">Student</th>
                  <th className="pb-3 text-left font-medium hidden sm:table-cell">Student ID</th>
                  <th className="pb-3 text-left font-medium">Course</th>
                  <th className="pb-3 text-left font-medium hidden md:table-cell">Centre</th>
                  <th className="pb-3 text-left font-medium hidden lg:table-cell">Enrolled</th>
                  <th className="pb-3 text-left font-medium">Status</th>
                  <th className="pb-3 text-right font-medium">Sign-off</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {students.map((app) => (
                  <tr key={app.id}>
                    <td className="py-3 font-medium text-gray-900">{app.applicant_name}</td>
                    <td className="py-3 text-gray-600 hidden sm:table-cell">{app.student_id ?? '—'}</td>
                    <td className="py-3 text-gray-600">{app.course_name}</td>
                    <td className="py-3 text-gray-600 hidden md:table-cell">{app.assigned_centre_name ?? '—'}</td>
                    <td className="py-3 text-gray-600 hidden lg:table-cell">
                      {app.enrolled_at ? format(new Date(app.enrolled_at), 'dd MMM yyyy') : '—'}
                    </td>
                    <td className="py-3"><Badge status={app.status} /></td>
                    <td className="py-3 text-right">
                      {app.lecturer_signed_off ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700">
                          <CheckCircle2 className="h-4 w-4" /> Signed off
                        </span>
                      ) : app.status === 'ENROLLED' ? (
                        <Button size="sm" onClick={() => setSignOffTarget(app)}>
                          Sign Off Completion
                        </Button>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <SignOffModal application={signOffTarget} onOpenChange={(open) => { if (!open) setSignOffTarget(null) }} />
    </AdminLayout>
  )
}
