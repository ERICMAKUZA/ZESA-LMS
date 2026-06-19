'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { CheckCircle, AlertCircle, CreditCard } from 'lucide-react'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'

interface PaymentDetail {
  id: string
  application: string
  amount: string
  currency: string
  method: string
  status: string
  course_name: string | null
}

export default function DemoPaymentPage({ params }: { params: { paymentId: string } }) {
  const { paymentId } = params
  const router = useRouter()
  const { toast } = useToast()
  const [confirmed, setConfirmed] = useState(false)

  const { data: payment, isLoading, isError } = useQuery<PaymentDetail>({
    queryKey: ['payment-status', paymentId],
    queryFn: async () => {
      const { data } = await api.get(`/payments/${paymentId}/status/`)
      return data
    },
  })

  const confirmMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/payments/${paymentId}/demo-confirm/`)
      return data as { application_status: string; moodle_course_url: string | null }
    },
    onSuccess: (data) => {
      setConfirmed(true)
      setTimeout(() => {
        toast({
          variant: 'success',
          title: 'Payment confirmed — enrollment in progress',
          description: data.application_status === 'ENROLLED' ? 'You are now enrolled in the course.' : undefined,
        })
        if (payment?.application) {
          router.push(`/applications/${payment.application}`)
        }
      }, 1500)
    },
  })

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      {/* Gateway header */}
      <div className="w-full max-w-lg">
        <div className="mb-6 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <CreditCard className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold text-gray-900">Demo Payment Gateway</span>
          </div>
          <span className="inline-flex items-center rounded-full bg-yellow-100 border border-yellow-300 px-3 py-1 text-xs font-semibold text-yellow-800">
            DEMO MODE — no real charge will occur
          </span>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white shadow-md overflow-hidden">
          {isLoading && (
            <div className="flex justify-center py-16">
              <Spinner size="lg" className="text-primary" />
            </div>
          )}

          {isError && (
            <div className="p-8 text-center">
              <AlertCircle className="mx-auto h-10 w-10 text-danger mb-3" />
              <p className="text-sm font-medium text-gray-700">Payment not found or unavailable.</p>
            </div>
          )}

          {payment && !confirmed && (
            <>
              <div className="border-b border-gray-100 bg-gray-50 px-6 py-4">
                <p className="text-xs uppercase tracking-wide text-gray-500 font-medium">Course</p>
                <p className="mt-1 text-lg font-semibold text-gray-900">{payment.course_name ?? 'ZESA Training Course'}</p>
              </div>

              <div className="px-6 py-6 flex flex-col gap-4">
                <div className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
                  <span className="text-sm text-gray-600">Amount due</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {payment.currency} {parseFloat(payment.amount).toFixed(2)}
                  </span>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Payment method</span>
                  <span className="font-medium text-gray-700">{payment.method}</span>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Reference</span>
                  <span className="font-mono text-xs text-gray-400">{paymentId.slice(0, 8).toUpperCase()}</span>
                </div>

                {confirmMutation.isError && (
                  <div className="flex items-start gap-2 rounded-md bg-red-50 border border-red-200 p-3">
                    <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-red-700 font-medium">Payment could not be confirmed.</p>
                      <button
                        onClick={() => confirmMutation.reset()}
                        className="mt-1 text-xs text-red-600 underline hover:no-underline"
                      >
                        Try again
                      </button>
                    </div>
                  </div>
                )}

                <Button
                  size="lg"
                  className="w-full mt-2"
                  onClick={() => confirmMutation.mutate()}
                  loading={confirmMutation.isPending}
                  disabled={confirmMutation.isError}
                >
                  Confirm Payment
                </Button>

                <p className="text-center text-xs text-gray-400">
                  This is a simulated payment. No funds will be transferred.
                </p>
              </div>
            </>
          )}

          {confirmed && (
            <div className="flex flex-col items-center gap-4 px-8 py-16 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <CheckCircle className="h-10 w-10 text-green-500 animate-in zoom-in duration-300" />
              </div>
              <p className="text-xl font-semibold text-gray-900">Payment Confirmed!</p>
              <p className="text-sm text-gray-500">Enrolling you in the course… redirecting</p>
              <Spinner className="text-primary" />
            </div>
          )}
        </div>

        <p className="mt-4 text-center text-xs text-gray-400">
          ZESA ILMP · Integrated Learning Management Platform
        </p>
      </div>
    </div>
  )
}
