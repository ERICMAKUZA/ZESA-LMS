'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import publicApi from '@/lib/publicApi'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import type { Course, PaginatedResponse } from '@/types'

const schema = z.object({
  full_name: z.string().min(2, 'Full name required'),
  email: z.string().email('Valid email required'),
  phone: z.string().optional(),
  organisation: z.string().optional(),
  enquiry_type: z.enum(['GENERAL', 'COURSE_INFO', 'FEES', 'ADMISSION', 'CORPORATE']),
  course: z.string().optional(),
  message: z.string().min(20, 'Please write at least 20 characters'),
})
type FormValues = z.infer<typeof schema>

const ENQUIRY_TYPES = [
  { value: 'GENERAL',     label: 'General Information' },
  { value: 'COURSE_INFO', label: 'Course Details & Requirements' },
  { value: 'FEES',        label: 'Fees & Payment' },
  { value: 'ADMISSION',   label: 'Admission & Application' },
  { value: 'CORPORATE',   label: 'Corporate / Group Booking' },
]

interface Props {
  open: boolean
  onClose: () => void
  preselectedCourse?: { id: string; fullname: string }
}

export default function EnquiryModal({ open, onClose, preselectedCourse }: Props) {
  const [successRef, setSuccessRef] = useState<string | null>(null)
  const [successEmail, setSuccessEmail] = useState('')

  const { data: coursesData } = useQuery<PaginatedResponse<Course>>({
    queryKey: ['courses-for-enquiry'],
    queryFn: () => publicApi.get('/courses/').then(r => r.data),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })
  const courses = coursesData?.results ?? []

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      enquiry_type: 'GENERAL',
      course: preselectedCourse ? String(preselectedCourse.id) : '',
    },
  })

  const enquiryType = watch('enquiry_type')
  const message = watch('message') ?? ''

  const onSubmit = async (values: FormValues) => {
    const payload = {
      ...values,
      course: values.course || null,
    }
    const { data } = await publicApi.post('/courses/enquiries/', payload)
    setSuccessEmail(values.email)
    setSuccessRef(data.ref)
  }

  const handleClose = () => {
    setSuccessRef(null)
    setSuccessEmail('')
    reset()
    onClose()
  }

  return (
    <Dialog.Root open={open} onOpenChange={(v) => { if (!v) handleClose() }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 flex flex-col max-h-[90vh]">
          {/* Header */}
          <div className="flex items-start justify-between px-6 pt-5 pb-4 border-b border-gray-100 shrink-0">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Make an Enquiry
            </Dialog.Title>
            <Dialog.Close className="rounded p-1 hover:bg-gray-100" onClick={handleClose}>
              <X className="h-5 w-5 text-gray-500" />
            </Dialog.Close>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-6 py-5">
            {successRef ? (
              <div className="text-center py-8">
                <div className="text-5xl mb-4 text-green-600">✓</div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Enquiry Received!</h3>
                <p className="text-sm text-gray-500 mb-1">
                  Reference: <strong>{successRef}</strong>
                </p>
                <p className="text-sm text-gray-500">
                  We will respond to <strong>{successEmail}</strong> within 2 business days.
                </p>
                <button onClick={handleClose} className="mt-6 text-green-700 font-medium text-sm hover:text-green-900">
                  Close
                </button>
              </div>
            ) : (
              <form id="enquiry-form" onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
                {/* Row 1: Name + Email */}
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Full Name *"
                    placeholder="Your full name"
                    error={errors.full_name?.message}
                    {...register('full_name')}
                  />
                  <Input
                    label="Email *"
                    type="email"
                    placeholder="you@example.com"
                    error={errors.email?.message}
                    {...register('email')}
                  />
                </div>

                {/* Row 2: Phone + Organisation (for CORPORATE) */}
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Phone"
                    type="tel"
                    placeholder="+263 7..."
                    {...register('phone')}
                  />
                  {enquiryType === 'CORPORATE' && (
                    <Input
                      label="Organisation"
                      placeholder="Company name"
                      {...register('organisation')}
                    />
                  )}
                </div>

                {/* Row 3: Enquiry Type */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Enquiry Type *</label>
                  <select
                    className="block w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-primary focus:ring-primary"
                    {...register('enquiry_type')}
                  >
                    {ENQUIRY_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  {errors.enquiry_type && (
                    <p className="text-xs text-red-600">{errors.enquiry_type.message}</p>
                  )}
                </div>

                {/* Row 4: Course */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">
                    Related Course <span className="text-gray-400 font-normal">(optional)</span>
                  </label>
                  <select
                    className="block w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-primary focus:ring-primary"
                    {...register('course')}
                  >
                    <option value="">— Not course-specific —</option>
                    {courses.map(c => (
                      <option key={c.id} value={String(c.id)}>{c.fullname}</option>
                    ))}
                  </select>
                </div>

                {/* Row 5: Message */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-gray-700">Message *</label>
                  <textarea
                    rows={4}
                    placeholder="Describe your enquiry in detail…"
                    className="block w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-primary focus:ring-primary resize-none"
                    {...register('message')}
                  />
                  <div className="flex justify-between">
                    {errors.message ? (
                      <p className="text-xs text-red-600">{errors.message.message}</p>
                    ) : (
                      <span />
                    )}
                    <span className={`text-xs ml-auto ${message.length < 20 ? 'text-gray-400' : 'text-green-700'}`}>
                      {message.length} / 20 min
                    </span>
                  </div>
                </div>
              </form>
            )}
          </div>

          {/* Footer */}
          {!successRef && (
            <div className="px-6 py-4 border-t border-gray-100 shrink-0">
              <Button
                type="submit"
                form="enquiry-form"
                className="w-full"
                loading={isSubmitting}
                disabled={isSubmitting}
              >
                Send Enquiry
              </Button>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
