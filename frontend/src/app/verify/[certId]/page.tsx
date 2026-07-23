'use client'

import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'
import PublicLayout from '@/components/layout/PublicLayout'
import Spinner from '@/components/ui/Spinner'
import Card from '@/components/ui/Card'

interface CertVerification {
  certificate_number: string
  valid: boolean
  holder_name: string
  student_id: string
  course: string
  course_shortname: string
  centre_name: string
  level_display: string
  issue_date: string
  issued_at: string
  status: 'VALID' | 'REVOKED'
  is_revoked: boolean
  revoked_at: string | null
  revocation_reason: string
  verification_url: string
}

function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-gray-500 flex-shrink-0">{label}</span>
      <span className={`text-gray-800 font-medium text-right ${mono ? 'font-mono text-primary' : ''}`}>
        {value}
      </span>
    </div>
  )
}

export default function VerifyCertPage({ params }: { params: { certId: string } }) {
  const { data, isLoading, error } = useQuery<CertVerification>({
    queryKey: ['cert-verify', params.certId],
    queryFn: async () => {
      const { data } = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL ?? '/api'}/certs/verify/${params.certId}/`,
      )
      return data
    },
    retry: false,
  })

  const notFoundDetail = axios.isAxiosError(error)
    ? (error.response?.data?.detail as string | undefined)
    : undefined

  return (
    <PublicLayout>
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="w-full max-w-md">
          {isLoading && (
            <div className="flex justify-center py-10">
              <Spinner size="lg" className="text-primary" />
            </div>
          )}

          {!isLoading && error && (
            <Card>
              <div className="flex flex-col items-center py-6 text-center">
                <XCircle className="h-12 w-12 text-danger mb-3" />
                <h2 className="text-lg font-semibold text-gray-900">Certificate Not Found</h2>
                <p className="mt-1 text-sm text-gray-600">
                  {notFoundDetail ?? 'This certificate could not be verified.'}
                </p>
                <p className="mt-4 text-xs text-gray-400">
                  Serial queried: <code className="font-mono">{params.certId}</code>
                </p>
              </div>
            </Card>
          )}

          {!isLoading && data?.is_revoked && (
            <Card>
              <div className="flex items-center gap-3 mb-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-red-100">
                  <XCircle className="h-6 w-6 text-danger" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-red-700">Certificate Revoked</h2>
                  <p className="text-sm text-red-500">
                    This certificate has been revoked and is no longer valid.
                  </p>
                </div>
              </div>
              <div className="bg-red-50 rounded-lg p-4 space-y-2 text-sm">
                <Row label="Certificate Number" value={data.certificate_number} mono />
                <Row label="Student" value={data.holder_name} />
                {data.revoked_at && (
                  <Row
                    label="Revoked On"
                    value={new Date(data.revoked_at).toLocaleDateString('en-GB', {
                      day: 'numeric', month: 'long', year: 'numeric',
                    })}
                  />
                )}
                {data.revocation_reason && <Row label="Reason" value={data.revocation_reason} />}
              </div>
            </Card>
          )}

          {!isLoading && data && !data.is_revoked && (
            <Card>
              <div className="flex items-center gap-3 mb-6">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-green-100">
                  <CheckCircle className="h-6 w-6 text-success" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-green-700">Certificate Verified</h2>
                  <p className="text-sm text-green-600">This is an authentic ZNTC certificate.</p>
                </div>
              </div>

              <div className="space-y-3 text-sm">
                <Row label="Certificate Number" value={data.certificate_number} mono />
                <Row label="Student Name" value={data.holder_name} />
                {data.student_id && <Row label="Student ID" value={data.student_id} mono />}
                <Row label="Course" value={data.course} />
                {data.level_display && <Row label="Programme" value={data.level_display} />}
                <Row label="Centre" value={data.centre_name} />
                <Row
                  label="Issue Date"
                  value={new Date(data.issued_at).toLocaleDateString('en-GB', {
                    day: 'numeric', month: 'long', year: 'numeric',
                  })}
                />
              </div>

              <div className="mt-6 pt-5 border-t border-gray-100 text-center">
                <p className="text-xs text-gray-400">
                  Verified by ZESA National Training Centre · HEXCO Accredited
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  For queries: training@zntc.ac.zw
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </PublicLayout>
  )
}
