'use client'

import { ArrowLeft, CheckCircle, Clock, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { format } from 'date-fns'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import StudentLayout from '@/components/layout/StudentLayout'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useApplication, useSubmitForReview } from '@/hooks/useApplications'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'
import type { ApplicationStatus, User } from '@/types'

const timelineStatuses: ApplicationStatus[] = [
  'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'PAYMENT_PENDING', 'PAYMENT_CONFIRMED', 'ENROLLED', 'CERTIFIED',
]

export default function ApplicationDetailPage({ params }: { params: { id: string } }) {
  const { data: app, isLoading } = useApplication(params.id)
  const submitMutation = useSubmitForReview(params.id)
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const router = useRouter()
  const [cocChecked, setCocChecked] = useState(false)

  const cocMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/my-applications/${params.id}/sign-code-of-conduct/`)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-applications', params.id] })
      toast({ variant: 'success', title: 'Code of conduct signed', description: 'You may now proceed with payment.' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Failed to sign', description: 'Please try again.' })
    },
  })

  const payNowMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/payments/initiate/${params.id}/`)
      return res.data as { redirect_url: string; payment_id: string }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['application', params.id] })
      if (data.redirect_url) {
        router.push(data.redirect_url)
      }
    },
    onError: () => {
      toast({ variant: 'error', title: 'Payment failed', description: 'Could not initiate payment. Please try again.' })
    },
  })

  const demoConfirmMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/payments/${app?.payment?.id}/demo-confirm/`)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', params.id] })
      toast({ variant: 'success', title: 'Payment confirmed', description: 'You are now enrolled in the course.' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Demo confirm failed', description: 'Please try again.' })
    },
  })

  const { data: me } = useQuery<User>({
    queryKey: ['me'],
    queryFn: () => api.get<User>('/users/me/').then(r => r.data),
  })

  const showCoCBanner =
    ['APPROVED', 'PAYMENT_PENDING', 'PAYMENT_CONFIRMED'].includes(app?.status ?? '') &&
    !app?.code_of_conduct_signed

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
      <div className="mb-4 flex items-center justify-between">
        <Link href="/applications" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary">
          <ArrowLeft className="h-4 w-4" /> Back to applications
        </Link>
        {app.ref && (
          <Link
            href={`/track/${app.ref}`}
            className="text-xs text-gray-400 hover:text-primary transition-colors"
          >
            Track without logging in: /track/{app.ref}
          </Link>
        )}
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

            {app.status === 'APPROVED' && (
              <div className="mt-4 rounded-md bg-green-50 border border-green-200 p-4">
                <p className="text-sm font-semibold text-green-800">Your application has been approved!</p>
                <p className="text-sm text-green-700 mt-1 mb-3">Complete your payment to secure your place on the course.</p>
                <Button onClick={() => payNowMutation.mutate()} loading={payNowMutation.isPending}>
                  Pay Now
                </Button>
              </div>
            )}

            {app.status === 'PAYMENT_PENDING' && app.payment && (
              <div className="mt-4 rounded-md bg-yellow-50 border border-yellow-200 p-4">
                <p className="text-sm font-semibold text-yellow-800">Payment pending</p>
                <p className="text-sm text-yellow-700 mt-1 mb-3">
                  Amount: <strong>{app.payment.currency} {app.payment.amount}</strong>. Click below to confirm your payment.
                </p>
                <Button
                  variant="secondary"
                  onClick={() => demoConfirmMutation.mutate()}
                  loading={demoConfirmMutation.isPending}
                >
                  Confirm Payment (Demo)
                </Button>
              </div>
            )}
          </Card>

          {/* Enrolled course card */}
          {app.status === 'ENROLLED' && app.enrollment && (
            <Card>
              <div className="flex items-center gap-3">
                <CheckCircle className="h-8 w-8 text-green-500 shrink-0" />
                <div>
                  <p className="font-semibold text-gray-900">You&apos;re enrolled!</p>
                  <p className="text-sm text-gray-500">Access your course on Moodle using the link below.</p>
                </div>
              </div>
              <div className="mt-4">
                <a
                  href={app.enrollment.moodle_course_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
                >
                  Go to your course <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </Card>
          )}

          {/* CoC banner — shown when approved/pending payment and not yet signed */}
          {showCoCBanner && (
            <div className="rounded-lg border-2 border-amber-400 bg-amber-50 p-5 mb-6">
              <div className="flex items-start gap-3">
                <span className="text-amber-500 text-xl mt-0.5">⚠</span>
                <div className="flex-1">
                  <p className="font-semibold text-amber-800 mb-1">
                    Action Required: Sign the Code of Conduct
                  </p>
                  <p className="text-sm text-amber-700 mb-4">
                    Before your enrolment can be confirmed, you must read and
                    acknowledge the ZNTC Code of Conduct. This is a mandatory step.
                  </p>
                  <a
                    href="/code-of-conduct.pdf"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-amber-700 underline mb-4 block"
                  >
                    Read the ZNTC Code of Conduct (PDF) →
                  </a>
                  <label className="flex items-center gap-2 cursor-pointer mb-4">
                    <input
                      type="checkbox"
                      checked={cocChecked}
                      onChange={(e) => setCocChecked(e.target.checked)}
                      className="w-4 h-4 accent-green-600"
                    />
                    <span className="text-sm text-gray-700">
                      I have read and agree to the ZNTC Code of Conduct
                    </span>
                  </label>
                  <Button
                    variant="primary"
                    disabled={!cocChecked || cocMutation.isPending}
                    loading={cocMutation.isPending}
                    onClick={() => cocMutation.mutate()}
                  >
                    Sign &amp; Continue
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* CoC confirmation strip — shown once signed */}
          {['APPROVED', 'PAYMENT_PENDING', 'PAYMENT_CONFIRMED'].includes(app.status) &&
            app.code_of_conduct_signed && (
            <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2 mb-6 text-sm">
              <span>✓</span>
              <span>
                Code of conduct signed on{' '}
                {new Date(app.code_of_conduct_signed_at!).toLocaleDateString('en-GB', {
                  day: 'numeric', month: 'long', year: 'numeric',
                })}
              </span>
            </div>
          )}

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

          {/* Enrolment confirmation panel — shown after enrolment */}
          {['ENROLLED', 'CERTIFIED'].includes(app.status) && me?.student_id && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-semibold text-green-800 mb-3">
                ✓ Enrolment Confirmed
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Student ID</span>
                  <span className="font-mono font-bold text-gray-800">{me.student_id}</span>
                </div>
                {me.zntc_email && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">ZNTC Email</span>
                    <span className="text-gray-800">{me.zntc_email}</span>
                  </div>
                )}
                <div className="pt-2">
                  <a
                    href={process.env.NEXT_PUBLIC_MOODLE_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-center bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-green-800 transition-colors"
                  >
                    Access Learning Portal (Moodle) →
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Details sidebar */}
        <div className="flex flex-col gap-4">
          {/* Programme */}
          <Card header={<h2 className="font-semibold text-gray-900">Programme Details</h2>}>
            <dl className="flex flex-col gap-3 text-sm">
              <div><dt className="text-xs text-gray-500">HEXCO Level</dt><dd className="text-gray-800 font-medium">{app.hexco_level || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Student Category</dt><dd className="text-gray-800 font-medium">{app.student_category || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Department</dt><dd className="text-gray-800">{app.department || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Employee ID</dt><dd className="text-gray-800">{app.employee_id || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Line Manager</dt><dd className="text-gray-800">{app.line_manager_email || '—'}</dd></div>
              {app.responsible_party && (
                <div><dt className="text-xs text-gray-500">Responsible Party</dt><dd className="text-gray-800">{app.responsible_party}</dd></div>
              )}
            </dl>
          </Card>

          {/* Accommodation */}
          <Card header={<h2 className="font-semibold text-gray-900">Accommodation</h2>}>
            <dl className="flex flex-col gap-3 text-sm">
              <div><dt className="text-xs text-gray-500">Residential</dt><dd className="text-gray-800 font-medium">{app.is_resident ? 'Yes' : 'No'}</dd></div>
              {app.is_resident && (
                <>
                  <div><dt className="text-xs text-gray-500">Hostel</dt><dd className="text-gray-800">{app.hostel_name || '—'}</dd></div>
                  <div><dt className="text-xs text-gray-500">Room</dt><dd className="text-gray-800">{app.room_number || '—'}</dd></div>
                </>
              )}
            </dl>
          </Card>

          {/* Guardian */}
          <Card header={<h2 className="font-semibold text-gray-900">Guardian / Next of Kin</h2>}>
            <dl className="flex flex-col gap-3 text-sm">
              <div><dt className="text-xs text-gray-500">Name</dt><dd className="text-gray-800">{app.guardian_name || '—'}</dd></div>
              <div><dt className="text-xs text-gray-500">Contact</dt><dd className="text-gray-800">{app.guardian_contact || '—'}</dd></div>
              {app.guardian_email && (
                <div><dt className="text-xs text-gray-500">Email</dt><dd className="text-gray-800">{app.guardian_email}</dd></div>
              )}
            </dl>
          </Card>

          {/* Motivation */}
          <Card header={<h2 className="font-semibold text-gray-900">Motivation</h2>}>
            <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">{app.motivation || '—'}</p>
          </Card>

          {/* Documents */}
          {(app.national_id_doc || app.academic_certs_doc || app.student_photo || app.documents.length > 0) && (
            <Card header={<h2 className="font-semibold text-gray-900">Documents</h2>}>
              <ul className="flex flex-col gap-2">
                {app.national_id_doc && (
                  <li>
                    <a href={app.national_id_doc} target="_blank" rel="noreferrer"
                       className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <span>📄</span> National ID / Passport
                    </a>
                  </li>
                )}
                {app.academic_certs_doc && (
                  <li>
                    <a href={app.academic_certs_doc} target="_blank" rel="noreferrer"
                       className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <span>📄</span> Academic Certificates
                    </a>
                  </li>
                )}
                {app.student_photo && (
                  <li>
                    <a href={app.student_photo} target="_blank" rel="noreferrer"
                       className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <span>🖼</span> Passport Photo
                    </a>
                  </li>
                )}
                {app.documents.map((doc) => (
                  <li key={doc.id}>
                    <a href={doc.file} target="_blank" rel="noreferrer"
                       className="flex items-center gap-2 text-sm text-primary hover:underline">
                      <span>📎</span> {doc.filename}
                    </a>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {app.payment && (
            <Card header={<h2 className="font-semibold text-gray-900">Payment</h2>}>
              <dl className="flex flex-col gap-3 text-sm">
                <div><dt className="text-xs text-gray-500">Amount</dt><dd className="text-gray-800">{app.payment.currency} {app.payment.amount}</dd></div>
                <div><dt className="text-xs text-gray-500">Method</dt><dd className="text-gray-800">{app.payment.method}</dd></div>
                <div><dt className="text-xs text-gray-500">Status</dt><dd><Badge status={app.payment.status as ApplicationStatus} /></dd></div>
                {app.payment.confirmed_at && (
                  <div><dt className="text-xs text-gray-500">Confirmed</dt><dd className="text-gray-800">{format(new Date(app.payment.confirmed_at), 'dd MMM yyyy HH:mm')}</dd></div>
                )}
              </dl>
            </Card>
          )}
        </div>
      </div>
    </StudentLayout>
  )
}
