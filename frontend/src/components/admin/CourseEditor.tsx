'use client'

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'
import type { Course, CourseCategory, User } from '@/types'

const levels = [
  { value: 'BEGINNER', label: 'Beginner' },
  { value: 'INTERMEDIATE', label: 'Intermediate' },
  { value: 'ADVANCED', label: 'Advanced' },
  { value: 'ALL_LEVELS', label: 'All levels' },
]

const months = [
  { value: '1', label: 'January' }, { value: '2', label: 'February' },
  { value: '3', label: 'March' }, { value: '4', label: 'April' },
  { value: '5', label: 'May' }, { value: '6', label: 'June' },
  { value: '7', label: 'July' }, { value: '8', label: 'August' },
  { value: '9', label: 'September' }, { value: '10', label: 'October' },
  { value: '11', label: 'November' }, { value: '12', label: 'December' },
]

const weeks = [
  { value: '1', label: 'Week 1' }, { value: '2', label: 'Week 2' },
  { value: '3', label: 'Week 3' }, { value: '4', label: 'Week 4' },
]

interface CourseEditorProps {
  course?: Course
}

export default function CourseEditor({ course }: CourseEditorProps) {
  const router = useRouter()
  const { toast } = useToast()
  const [form, setForm] = useState({
    shortname: course?.shortname ?? '',
    fullname: course?.fullname ?? '',
    summary: course?.summary ?? '',
    categoryId: course?.category?.id ? String(course.category.id) : '',
    durationDays: course?.duration_days ? String(course.duration_days) : '',
    level: course?.level ?? '',
    price: course?.price ?? '',
    maxCapacity: course?.max_capacity ? String(course.max_capacity) : '',
    thumbnailUrl: course?.thumbnail_url ?? '',
    isActive: course?.is_active ?? true,
    requiresApproval: course?.requires_approval ?? true,
    intakeYear: String(new Date().getFullYear()),
    intakeMonth: '',
    intakeWeek: '',
    intakeCapacity: course?.max_capacity ? String(course.max_capacity) : '',
    intakeNotes: '',
  })
  const [lecturerIds, setLecturerIds] = useState<number[]>(course?.lecturers.map((lecturer) => lecturer.id) ?? [])
  const [assignmentError, setAssignmentError] = useState('')
  const [intakeError, setIntakeError] = useState('')

  const categoriesQuery = useQuery<CourseCategory[]>({
    queryKey: ['course-categories'],
    queryFn: async () => (await api.get('/courses/categories/')).data,
  })
  const lecturersQuery = useQuery<User[]>({
    queryKey: ['active-lecturers'],
    queryFn: async () => (await api.get('/admin/lecturers/')).data,
  })

  const saveCourse = useMutation({
    mutationFn: async () => {
      const payload = {
        shortname: form.shortname.trim(),
        fullname: form.fullname.trim(),
        summary: form.summary.trim(),
        category_id: Number(form.categoryId),
        duration_days: form.durationDays ? Number(form.durationDays) : null,
        level: form.level || null,
        price: form.price ? Number(form.price) : null,
        max_capacity: form.maxCapacity ? Number(form.maxCapacity) : null,
        thumbnail_url: form.thumbnailUrl.trim(),
        is_active: form.isActive,
        requires_approval: form.requiresApproval,
        lecturer_ids: lecturerIds,
        ...(!course && {
          initial_schedule: {
            year: Number(form.intakeYear),
            month: Number(form.intakeMonth),
            week_in_month: Number(form.intakeWeek),
            max_capacity: Number(form.intakeCapacity || form.maxCapacity),
            notes: form.intakeNotes.trim(),
          },
        }),
      }
      if (course) {
        return api.patch(`/courses/admin/${course.id}/`, payload)
      }
      return api.post('/courses/admin/', payload)
    },
    onSuccess: () => {
      toast({
        variant: 'success',
        title: course ? 'Course updated' : 'Course created',
        description: course
          ? 'The portal and Moodle course details have been updated.'
          : 'The course is ready for applications and lecturer operations.',
      })
      router.push('/admin/courses')
    },
    onError: () => {
      toast({
        variant: 'error',
        title: course ? 'Could not update course' : 'Could not create course',
        description: 'Check the course details and Moodle connection, then try again.',
      })
    },
  })

  const setField = (field: keyof typeof form, value: string | boolean) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const toggleLecturer = (lecturerId: number) => {
    setAssignmentError('')
    setLecturerIds((current) => (
      current.includes(lecturerId)
        ? current.filter((id) => id !== lecturerId)
        : [...current, lecturerId]
    ))
  }

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (lecturerIds.length === 0) {
      setAssignmentError('Assign at least one lecturer before saving this course.')
      return
    }
    if (!course && (!form.intakeYear || !form.intakeMonth || !form.intakeWeek || !(form.intakeCapacity || form.maxCapacity))) {
      setIntakeError('Add the date and capacity for the first course intake.')
      return
    }
    setIntakeError('')
    saveCourse.mutate()
  }

  const categories = categoriesQuery.data ?? []
  const lecturers = lecturersQuery.data ?? []
  const isLoading = categoriesQuery.isLoading || lecturersQuery.isLoading

  return (
    <form onSubmit={submit} className="mx-auto max-w-5xl space-y-6">
      <Card>
        <div className="mb-5">
          <h2 className="text-base font-semibold text-gray-900">Course Details</h2>
          <p className="mt-1 text-sm text-gray-500">These details appear in the portal and are published to Moodle.</p>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-10"><Spinner className="text-primary" /></div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2">
            <Input label="Course title *" value={form.fullname} onChange={(event) => setField('fullname', event.target.value)} required />
            <Input label="Course code *" value={form.shortname} onChange={(event) => setField('shortname', event.target.value)} helper="Use a short, unique code, for example ELEC-101." required />
            <Select label="Category *" value={form.categoryId} onValueChange={(value) => setField('categoryId', value)} options={categories.map((category) => ({ value: String(category.id), label: category.name }))} placeholder="Select a category" />
            <Select label="Level" value={form.level} onValueChange={(value) => setField('level', value)} options={levels} placeholder="Select a level" />
            <Input label="Duration (days)" type="number" min="1" value={form.durationDays} onChange={(event) => setField('durationDays', event.target.value)} />
            <Input label="Fee (USD)" type="number" min="0" step="0.01" value={form.price} onChange={(event) => setField('price', event.target.value)} />
            <Input label="Maximum class size" type="number" min="1" value={form.maxCapacity} onChange={(event) => setField('maxCapacity', event.target.value)} />
            <Input label="Course image URL" type="url" value={form.thumbnailUrl} onChange={(event) => setField('thumbnailUrl', event.target.value)} />
            <div className="md:col-span-2 flex flex-col gap-1">
              <label htmlFor="course-summary" className="text-sm font-medium text-gray-700">Course description</label>
              <textarea id="course-summary" rows={5} value={form.summary} onChange={(event) => setField('summary', event.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>
          </div>
        )}
      </Card>

      {!course && (
        <Card>
          <div className="mb-5">
            <h2 className="text-base font-semibold text-gray-900">First Course Intake *</h2>
            <p className="mt-1 text-sm text-gray-500">Set the first available training period so students can apply and lecturers can manage the course.</p>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            <Input label="Year *" type="number" min="2020" value={form.intakeYear} onChange={(event) => setField('intakeYear', event.target.value)} required />
            <Select label="Month *" value={form.intakeMonth} onValueChange={(value) => setField('intakeMonth', value)} options={months} placeholder="Select month" />
            <Select label="Week *" value={form.intakeWeek} onValueChange={(value) => setField('intakeWeek', value)} options={weeks} placeholder="Select week" />
            <Input label="Intake capacity *" type="number" min="1" value={form.intakeCapacity} onChange={(event) => setField('intakeCapacity', event.target.value)} helper="Defaults to the course capacity if left blank." />
            <div className="md:col-span-2 lg:col-span-4 flex flex-col gap-1">
              <label htmlFor="intake-notes" className="text-sm font-medium text-gray-700">Intake notes</label>
              <textarea id="intake-notes" rows={3} value={form.intakeNotes} onChange={(event) => setField('intakeNotes', event.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary" placeholder="Optional location, equipment, or preparation notes." />
            </div>
          </div>
          {intakeError && <p className="mt-3 text-sm text-danger">{intakeError}</p>}
        </Card>
      )}

      <Card>
        <div className="mb-5">
          <h2 className="text-base font-semibold text-gray-900">Assigned Lecturers *</h2>
          <p className="mt-1 text-sm text-gray-500">Every selected lecturer can manage students and course operations for this course.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {lecturers.map((lecturer) => {
            const selected = lecturerIds.includes(lecturer.id)
            return (
              <label key={lecturer.id} className={`flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors ${selected ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-primary/50'}`}>
                <input type="checkbox" checked={selected} onChange={() => toggleLecturer(lecturer.id)} className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
                <span>
                  <span className="block font-medium text-gray-900">{lecturer.full_name}</span>
                  <span className="block text-sm text-gray-500">{lecturer.email}</span>
                </span>
              </label>
            )
          })}
        </div>
        {!isLoading && lecturers.length === 0 && <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">No active lecturer accounts are available. Create or activate a lecturer account first.</p>}
        {assignmentError && <p className="mt-3 text-sm text-danger">{assignmentError}</p>}
      </Card>

      <Card>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" checked={form.isActive} onChange={(event) => setField('isActive', event.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" /> Publish this course</label>
            <label className="flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" checked={form.requiresApproval} onChange={(event) => setField('requiresApproval', event.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" /> Require application approval before enrolment</label>
          </div>
          <div className="flex gap-3">
            <Button type="button" variant="outline" onClick={() => router.push('/admin/courses')}>Cancel</Button>
            <Button type="submit" loading={saveCourse.isPending} disabled={isLoading || lecturers.length === 0}>{course ? 'Save Changes' : 'Create Course'}</Button>
          </div>
        </div>
      </Card>
    </form>
  )
}
