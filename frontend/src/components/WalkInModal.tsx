'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'
import type { Centre } from '@/types'
import QualificationFields, { emptySelection, validateQualificationSelection, type QualificationSelection, type TrainingCourse } from '@/components/applications/QualificationFields'

const schema = z.object({
  student_first_name: z.string().min(1, 'Required'),
  student_last_name:  z.string().min(1, 'Required'),
  student_email:      z.string().email('Enter a valid email'),
  student_phone:      z.string().min(9, 'Enter a valid phone number'),
  course:             z.string().min(1, 'Select a course'),
  student_category:   z.enum(['DIRECT', 'APPRENTICE', 'INTERNAL']),
  preferred_centre:   z.string().min(1, 'Select a centre'),
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onClose: () => void
}

export default function WalkInModal({ open, onClose }: Props) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [qualification, setQualification] = useState<QualificationSelection>(emptySelection)
  const [qualificationError, setQualificationError] = useState<string | null>(null)

  const { data: centres = [] } = useQuery<Centre[]>({
    queryKey: ['centres'],
    queryFn: () => api.get<Centre[]>('/centres/').then(r => r.data),
    enabled: open,
  })

  const { data: courses = [] } = useQuery<TrainingCourse[]>({
    queryKey: ['training-selection'],
    queryFn: () => api.get<TrainingCourse[]>('/courses/training/selection/').then(r => r.data),
    enabled: open,
  })

  const { register, setValue, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { course: '', student_category: 'DIRECT' },
  })

  const mutation = useMutation({
    mutationFn: (data: FormValues & QualificationSelection) =>
      api.post<{ id: string; ref: string; status: string }>('/admin/applications/walk-in/', data),
    onSuccess: ({ data }) => {
      toast({ variant: 'success', title: `Walk-in registered — Ref: ${data.ref}` })
      queryClient.invalidateQueries({ queryKey: ['admin-applications'] })
      reset()
      setQualification(emptySelection)
      onClose()
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data
      const msg = typeof data?.detail === 'string' ? data.detail : data ? Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`).join(' · ') : 'Check the details and try again.'
      toast({ variant: 'error', title: 'Registration failed', description: msg })
    },
  })

  const onSubmit = (values: FormValues) => {
    const course = courses.find(item => String(item.id) === qualification.course)
    const error = validateQualificationSelection(qualification, course)
    if (error) {
      setQualificationError(error)
      return
    }
    setQualificationError(null)
    mutation.mutate({ ...values, ...qualification })
  }

  const close = () => { reset(); setQualification(emptySelection); setQualificationError(null); onClose() }

  return (
    <Modal
      open={open}
      onOpenChange={(o) => { if (!o) close() }}
      title="Register Walk-in Student"
      footer={
        <>
          <Button variant="ghost" onClick={close}>Cancel</Button>
          <Button variant="primary" loading={isSubmitting || mutation.isPending} onClick={handleSubmit(onSubmit)}>
            Register
          </Button>
        </>
      }
    >
      <form className="flex flex-col gap-4">
        {/* Row 1: names */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input label="First Name" error={errors.student_first_name?.message} {...register('student_first_name')} />
          <Input label="Last Name"  error={errors.student_last_name?.message}  {...register('student_last_name')} />
        </div>

        {/* Row 2: contact */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Input label="Email" type="email" error={errors.student_email?.message} {...register('student_email')} />
          <Input label="Phone" type="tel"   error={errors.student_phone?.message} placeholder="+263 77 123 4567" {...register('student_phone')} />
        </div>

        <QualificationFields value={qualification} onChange={next => {
          setQualification(next)
          setValue('course', next.course, { shouldValidate: true })
          setQualificationError(null)
        }} error={qualificationError ?? errors.course?.message} />

        {/* Row 5: category + centre */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Student Category <span className="text-red-500">*</span>
            </label>
            <select
              {...register('student_category')}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="DIRECT">Direct</option>
              <option value="APPRENTICE">Apprentice</option>
              <option value="INTERNAL">Internal</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preferred Centre <span className="text-red-500">*</span>
            </label>
            <select
              {...register('preferred_centre')}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">— Select a centre —</option>
              {centres.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name}{c.is_primary ? ' (Primary)' : ''} — {c.location}
                </option>
              ))}
            </select>
            {errors.preferred_centre && <p className="text-red-500 text-xs mt-1">{errors.preferred_centre.message}</p>}
          </div>
        </div>
      </form>
    </Modal>
  )
}
