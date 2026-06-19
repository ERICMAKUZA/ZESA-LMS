'use client'

import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'
import PublicLayout from '@/components/layout/PublicLayout'
import Spinner from '@/components/ui/Spinner'
import Card from '@/components/ui/Card'

interface CertVerification {
  valid: boolean
  holder_name: string
  course: string
  issued_at: string
  status: 'VALID' | 'REVOKED'
}

export default function VerifyCertPage({ params }: { params: { certId: string } }) {
  const { data, isLoading, isError } = useQuery<CertVerification>({
    queryKey: ['cert-verify', params.certId],
    queryFn: async () => {
      const { data } = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL ?? '/api'}/certs/verify/${params.certId}/`,
      )
      return data
    },
  })

  return (
    <PublicLayout>
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="w-full max-w-md">
          {isLoading && (
            <div className="flex justify-center py-10">
              <Spinner size="lg" className="text-primary" />
            </div>
          )}
          {isError && (
            <Card>
              <div className="flex flex-col items-center py-6 text-center">
                <XCircle className="h-12 w-12 text-danger mb-3" />
                <h2 className="text-lg font-semibold text-gray-900">Certificate not found</h2>
                <p className="mt-1 text-sm text-gray-600">
                  The certificate ID <code className="font-mono text-xs">{params.certId}</code> could not be verified.
                </p>
              </div>
            </Card>
          )}
          {data && (
            <Card>
              <div className="flex flex-col items-center py-6 text-center">
                {data.status === 'VALID' ? (
                  <CheckCircle className="h-14 w-14 text-success mb-3" />
                ) : (
                  <XCircle className="h-14 w-14 text-danger mb-3" />
                )}
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    data.status === 'VALID'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {data.status}
                </span>
                <h2 className="mt-4 text-xl font-bold text-gray-900">{data.holder_name}</h2>
                <p className="mt-1 text-sm text-gray-600">has completed</p>
                <p className="mt-1 text-base font-semibold text-primary">{data.course}</p>
                <p className="mt-3 text-xs text-gray-400">
                  Issued: {new Date(data.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
                </p>
                <p className="mt-4 text-xs text-gray-400">
                  Certificate ID: <code className="font-mono">{params.certId}</code>
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </PublicLayout>
  )
}
