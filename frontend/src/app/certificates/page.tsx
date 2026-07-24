'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Award, ExternalLink } from 'lucide-react'
import { format } from 'date-fns'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useMyCertificates } from '@/hooks/useCertificates'
import api from '@/lib/api'

export default function CertificatesPage() {
  const { data, isLoading } = useMyCertificates()
  const certificates = data?.results ?? []
  const { toast } = useToast()
  const [printingId, setPrintingId] = useState<string | null>(null)

  const handlePrintDuplicate = async (certId: string, certificateNumber: string) => {
    setPrintingId(certId)
    try {
      const response = await api.get(`/certs/${certId}/download/`, {
        params: { duplicate: 'true' },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `${certificateNumber}_DUPLICATE.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast({ variant: 'error', title: 'Failed to generate duplicate copy' })
    } finally {
      setPrintingId(null)
    }
  }

  return (
    <StudentLayout>
      <PageHeader
        title="My Certificates"
        subtitle="Certificates earned from completed courses."
      />

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && certificates.length === 0 && (
          <div className="flex flex-col items-center py-12 text-center">
            <Award className="h-12 w-12 text-gray-300 mb-3" />
            <p className="text-sm text-gray-500">No certificates yet.</p>
            <p className="mt-1 text-xs text-gray-400">
              Complete an enrolled course to earn your first certificate.
            </p>
            <Link href="/courses" className="mt-4 text-sm text-primary hover:underline">
              Browse courses
            </Link>
          </div>
        )}

        {!isLoading && certificates.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {certificates.map((cert) => (
              <div
                key={cert.id}
                className="rounded-lg border border-gray-200 p-4 flex flex-col gap-3"
              >
                <div className="flex items-start gap-3">
                  <Award className="h-8 w-8 text-accent shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm leading-snug">
                      {cert.course_detail.fullname}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Issued {format(new Date(cert.issued_at), 'dd MMM yyyy')}
                    </p>
                  </div>
                  {cert.is_revoked && (
                    <span className="shrink-0 rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700">
                      Revoked
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-gray-400">{cert.certificate_number}</span>
                  <div className="flex items-center gap-3">
                    {cert.pdf_url && (
                      <a
                        href={cert.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        Download
                      </a>
                    )}
                    <button
                      onClick={() => handlePrintDuplicate(cert.id, cert.certificate_number)}
                      disabled={printingId === cert.id}
                      className="text-xs text-amber-700 border border-amber-200 px-2 py-1 rounded hover:bg-amber-50 disabled:opacity-50"
                    >
                      {printingId === cert.id ? 'Generating…' : 'Print Duplicate'}
                    </button>
                    <Link
                      href={`/verify/${cert.certificate_number}`}
                      className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      Verify <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </StudentLayout>
  )
}
