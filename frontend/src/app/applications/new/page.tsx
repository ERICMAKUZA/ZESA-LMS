'use client'

import { Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useSubmitApplication, useSubmitForReview } from '@/hooks/useApplications'
import { useCourse } from '@/hooks/useCourses'
import { useAuth } from '@/hooks/useAuth'
import { useState } from 'react'

const schema = z.object({
  motivation: z.string().min(50, 'Please provide at least 50 characters explaining your motivation.'),
  line_manager_email: z.string().email('Enter a valid email address'),
  department: z.string().min(1, 'Department is required'),
  employee_id: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

function NewApplicationForm() {
  const searchParams = useSearchParams()
  const courseId = searchParams.get('courseId') ?? ''
  const router = useRouter()
  const { user } = useAuth()
  const { toast } = useToast()
  const { data: course, isLoading: courseLoading } = useCourse(courseId)
  const submitApplication = useSubmitApplication()
  const [createdId, setCreatedId] = useState<string | null>(null)
  const submitForReview = useSubmitForReview(createdId ?? '')

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { department: user?.full_name ? '' : '' },
  })

  const onSubmit = async (values: FormValues) => {
    try {
      const app = await submitApplication.mutateAsync({
        course: Number(courseId),
        ...values,
      })
      setCreatedId(app.id)
      await submitForReview.mutateAsync()
      toast({ variant: 'success', title: 'Application submitted!', description: 'A reviewer will assess your application.' })
      router.push('/applications')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({ variant: 'error', title: 'Submission failed', description: msg ?? 'Please check your details.' })
    }
  }

  return (
    <>
      <PageHeader
        title="New Application"
        subtitle={course ? `Applying for: ${course.fullname}` : 'Loading���'}
      />

      {courseLoading && (
        <div className="flex justify-center py-10"><Spinner className="text-primary" /></div>
      )}

      {!courseLoading && !course && (
        <p className="text-center text-sm text-gray-500 py-10">Course not found. Please go back and try again.</p>
      )}

      {course && (
        <Card className="max-w-2xl">
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Motivation <span className="text-gray-400 font-normal">(min 50 characters)</span>
              </label>
              <textarea
                rows={5}
                className="block w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-primary focus:ring-primary"
                placeholder="Explain why you want to enrol in this course and how it relates to your role…"
                {...register('motivation')}
              />
              {errors.motivation && <p className="mt-1 text-xs text-danger">{errors.motivation.message}</p>}
            </div>

            <Input
              label="Line Manager Email"
              type="email"
              error={errors.line_manager_email?.message}
              helper="Your line manager will be notified of this application."
              {...register('line_manager_email')}
            />
            <Input
              label="Department"
              error={errors.department?.message}
              {...register('department')}
            />
            <Input
              label="Employee ID"
              error={errors.employee_id?.message}
              helper="Leave blank to use the ID on your profile."
              {...register('employee_id')}
            />

            <div className="flex gap-3 pt-2">
              <Button type="submit" loading={isSubmitting || submitApplication.isPending || submitForReview.isPending}>
                Submit Application
              </Button>
              <Button type="button" variant="ghost" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}
    </>
  )
}

export default function NewApplicationPage() {
  return (
    <StudentLayout>
      <Suspense fallback={<div className="flex justify-center py-10"><Spinner className="text-primary" /></div>}>
        <NewApplicationForm />
      </Suspense>
    </StudentLayout>
  )
}
