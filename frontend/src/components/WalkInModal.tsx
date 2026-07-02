'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'
import type { Centre, Course } from '@/types'

const schema = z.object({
  student_first_name: z.string().min(1, 'Required'),
  student_last_name:  z.string().min(1, 'Required'),
  student_email:      z.string().email('Enter a valid email'),
  student_phone:      z.string().min(9, 'Enter a valid phone number'),
  course:             z.string().min(1, 'Select a course'),
  hexco_level:        z.enum(['NC', 'ND']),
  department:         z.enum(['ELECTRICAL', 'TELECOMS', 'MECHANICAL']),
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

  const { data: centres = [] } = useQuery<Centre[]>({
    queryKey: ['centres'],
    queryFn: () => api.get<Centre[]>('/centres/').then(r => r.data),
    enabled: open,
  })

  const { data: courses = [] } = useQuery<Course[]>({
    queryKey: ['courses-approval'],
    queryFn: () =>
      api.get<{ results: Course[] }>('/courses/?requires_approval=true&is_active=true')
        .then(r => r.data.results ?? (r.data as unknown as Course[])),
    enabled: open,
  })

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { hexco_level: 'NC', department: 'ELECTRICAL', student_category: 'DIRECT' },
  })

  const mutation = useMutation({
    mutationFn: (data: FormValues) =>
      api.post<{ id: string; ref: string; status: string }>('/admin/applications/walk-in/', data),
    onSuccess: ({ data }) => {
      toast({ variant: 'success', title: `Walk-in registered — Ref: ${data.ref}` })
      queryClient.invalidateQueries({ queryKey: ['admin-applications'] })
      reset()
      onClose()
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ variant: 'error', title: 'Registration failed', description: msg })
    },
  })

  const onSubmit = (values: FormValues) => mutation.mutate(values)

  return (
    <Modal
      open={open}
      onOpenChange={(o) => { if (!o) { reset(); onClose() } }}
      title="Register Walk-in Student"
      footer={
        <>
          <Button variant="ghost" onClick={() => { reset(); onClose() }}>Cancel</Button>
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

        {/* Row 3: course */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Course <span className="text-red-500">*</span>
          </label>
          <select
            {...register('course')}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">— Select a course —</option>
            {courses.map(c => (
              <option key={c.id} value={String(c.id)}>{c.fullname}</option>
            ))}
          </select>
          {errors.course && <p className="text-red-500 text-xs mt-1">{errors.course.message}</p>}
        </div>

        {/* Row 4: HEXCO level + department */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <p className="block text-sm font-medium text-gray-700 mb-1">
              HEXCO Level <span className="text-red-500">*</span>
            </p>
            <div className="flex gap-3">
              {(['NC', 'ND'] as const).map(v => (
                <label key={v} className="flex items-center gap-1.5 cursor-pointer text-sm">
                  <input type="radio" value={v} {...register('hexco_level')} className="accent-primary" />
                  {v}
                </label>
              ))}
            </div>
            {errors.hexco_level && <p className="text-red-500 text-xs mt-1">{errors.hexco_level.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department <span className="text-red-500">*</span>
            </label>
            <select
              {...register('department')}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="ELECTRICAL">Electrical</option>
              <option value="TELECOMS">Telecoms</option>
              <option value="MECHANICAL">Mechanical</option>
            </select>
          </div>
        </div>

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
