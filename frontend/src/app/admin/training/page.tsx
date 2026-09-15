'use client'

import { useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { CalendarDays, ExternalLink, Send } from 'lucide-react'
import AdminLayout from '@/components/layout/AdminLayout'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/hooks/useAuth'
import api from '@/lib/api'

interface PaginatedResponse<T> {
  results: T[]
  next: string | null
}

interface CourseOption {
  id: number
  shortname: string
  fullname: string
  is_active: boolean
  upcoming_schedules?: Array<{
    id: string
    approximate_start_date: string
    approximate_end_date: string
  }>
}

interface CalendarEvent {
  id: string
  event_type: string
  title: string
  start_date: string
  end_date: string | null
  audience: 'STUDENTS' | 'LECTURERS' | 'BOTH'
  course: number | null
  schedule: string | null
  timetable_url: string
  published_at: string
}

interface EventOption {
  value: string
  label: string
}

interface EventForm {
  event_type: string
  title: string
  start_date: string
  end_date: string
  audience: CalendarEvent['audience']
  course: string
  schedule: string
  timetable_url: string
}

const documentedEventTypes: EventOption[] = [
  { value: 'COMMENCEMENT', label: 'Commencement' },
  { value: 'DEFERMENT', label: 'Course deferment' },
  { value: 'EXAMINATION', label: 'Examination' },
  { value: 'SEMESTER_START', label: 'Semester start' },
  { value: 'SEMESTER_END', label: 'Semester end' },
  { value: 'BLOCK_START', label: 'Block start' },
  { value: 'BLOCK_END', label: 'Block end' },
  { value: 'SEMESTER_BREAK', label: 'Semester break' },
  { value: 'EXAM_FEE', label: 'Examination fee' },
  { value: 'MARKS_DEADLINE', label: 'Marks deadline' },
]

const rangedTypes = new Set(['EXAMINATION', 'SEMESTER_START', 'SEMESTER_END', 'BLOCK_START', 'BLOCK_END', 'SEMESTER_BREAK'])
const emptyForm: EventForm = {
  event_type: '', title: '', start_date: '', end_date: '', audience: 'STUDENTS',
  course: '', schedule: '', timetable_url: '',
}
const selectClass = 'block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-primary focus:ring-primary'

async function fetchAll<T>(path: string): Promise<T[]> {
  const items: T[] = []
  let next: string | null = path
  while (next) {
    const { data }: { data: T[] | PaginatedResponse<T> } = await api.get(next)
    if (Array.isArray(data)) return [...items, ...data]
    items.push(...data.results)
    next = data.next
  }
  return items
}

function readableDate(value: string) {
  return format(parseISO(value), 'd MMM yyyy')
}

function apiErrors(error: unknown): Record<string, string> {
  if (isAxiosError(error) && error.response?.data) {
    const data: unknown = error.response.data
    if (typeof data === 'string') return { form: data }
    if (data && typeof data === 'object') {
      const entries = Object.entries(data).map(([key, value]) => [
        key === 'detail' || key === 'non_field_errors' ? 'form' : key,
        Array.isArray(value) ? value.join(', ') : String(value),
      ])
      return Object.fromEntries(entries)
    }
  }
  return { form: error instanceof Error ? error.message : 'Please try again.' }
}

function errorSummary(error: unknown): string {
  const details = apiErrors(error)
  return details.form ?? Object.values(details).join(' · ')
}

function validHttpUrl(value: string) {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' || url.protocol === 'http:'
  } catch {
    return false
  }
}

function validate(form: EventForm): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!form.event_type) errors.event_type = 'Choose an event type.'
  if (!form.title.trim()) errors.title = 'Enter a title.'
  if (!form.start_date) errors.start_date = 'Choose a start date.'
  if (rangedTypes.has(form.event_type) && !form.end_date) errors.end_date = 'This event needs an end date.'
  if (form.start_date && form.end_date && form.end_date < form.start_date) errors.end_date = 'End date cannot precede start date.'
  if (form.event_type === 'EXAMINATION' && !form.timetable_url.trim()) errors.timetable_url = 'Examinations need a timetable link.'
  if (['COMMENCEMENT', 'DEFERMENT'].includes(form.event_type) && !form.course) errors.course = 'Choose the affected course.'
  if (form.event_type === 'COMMENCEMENT' && !form.schedule) errors.schedule = 'Choose the intake that is commencing.'
  if (form.event_type === 'DEFERMENT' && form.end_date && form.end_date <= form.start_date) errors.end_date = 'The new date must be after the original date.'
  if (form.timetable_url.trim() && !validHttpUrl(form.timetable_url.trim())) errors.timetable_url = 'Enter a valid http or https link.'
  return errors
}

export default function AdminTrainingPage() {
  const { user } = useAuth()
  const manager = user?.role === 'TRAINER' || user?.role === 'ADMIN' || user?.role === 'SUPERADMIN'
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [form, setForm] = useState<EventForm>(emptyForm)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const coursesQuery = useQuery({
    queryKey: ['calendar-courses'],
    queryFn: () => fetchAll<CourseOption>('/courses/admin/'),
    enabled: manager,
  })
  const eventsQuery = useQuery({
    queryKey: ['calendar-events'],
    queryFn: () => fetchAll<CalendarEvent>('/courses/calendar-events/'),
    enabled: manager,
  })
  const optionsQuery = useQuery({
    queryKey: ['calendar-event-options'],
    queryFn: async (): Promise<EventOption[]> => {
      const { data } = await api.options('/courses/calendar-events/')
      const choices: unknown = data?.actions?.POST?.event_type?.choices
      if (!Array.isArray(choices)) return documentedEventTypes
      const options = choices.filter((choice): choice is { value: string; display_name: string } => (
        typeof choice?.value === 'string' && typeof choice?.display_name === 'string'
      ))
      return options.length ? options.map((choice) => ({ value: choice.value, label: choice.display_name })) : documentedEventTypes
    },
    enabled: manager,
  })
  const eventTypes = optionsQuery.data ?? documentedEventTypes
  const courses = coursesQuery.data ?? []
  const selectedCourse = courses.find((course) => String(course.id) === form.course)
  const availableSchedules = selectedCourse?.upcoming_schedules ?? []
  const events = eventsQuery.data ?? []

  const publish = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.post('/courses/calendar-events/', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      setForm(emptyForm)
      setErrors({})
      toast({ variant: 'success', title: 'Calendar event published' })
    },
    onError: (error) => setErrors(apiErrors(error)),
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = validate(form)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return

    const target = selectedCourse?.fullname ?? 'all eligible recipients'
    if (!window.confirm(`Publish ${eventTypes.find((item) => item.value === form.event_type)?.label ?? form.event_type} for ${target}? This sends notifications immediately.`)) return

    publish.mutate({
      event_type: form.event_type,
      title: form.title.trim(),
      start_date: form.start_date,
      end_date: form.end_date || null,
      audience: form.audience,
      course: form.course ? Number(form.course) : null,
      schedule: form.schedule || null,
      timetable_url: form.timetable_url.trim(),
    })
  }

  return (
    <AdminLayout>
      <PageHeader title="Training Calendar" subtitle="Publish lifecycle dates and notify the relevant training audience." />
      {!manager ? (
        <Card><p className="py-10 text-center text-sm text-gray-600">Only training managers can publish calendar events.</p></Card>
      ) : (
        <div className="space-y-6">
          <Card>
            <div className="mb-5 flex items-start gap-3">
              <CalendarDays className="mt-0.5 h-5 w-5 text-primary" />
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Publish an event</h2>
                <p className="text-sm text-gray-500">Publication sends notifications immediately. Check the audience and dates before confirming.</p>
              </div>
            </div>
            {errors.form && <p role="alert" className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{errors.form}</p>}
            {coursesQuery.isError && <p role="alert" className="mb-4 text-sm text-red-700">Could not load courses: {errorSummary(coursesQuery.error)}</p>}
            {optionsQuery.isError && <p role="status" className="mb-4 text-sm text-amber-700">Could not load the latest event types. Showing the locally known types.</p>}
            <form onSubmit={submit} noValidate className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Event type
                  <select className={selectClass} value={form.event_type} onChange={(event) => {
                    const eventType = event.target.value
                    setForm({ ...form, event_type: eventType, audience: eventType === 'EXAMINATION' || eventType === 'MARKS_DEADLINE' ? 'BOTH' : 'STUDENTS' })
                  }}>
                    <option value="">Select event type</option>
                    {eventTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                  {errors.event_type && <span className="text-xs text-red-700">{errors.event_type}</span>}
                </label>
                <Input id="calendar-title" label="Title" maxLength={255} value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} error={errors.title} placeholder="e.g. November examinations" />
                <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">{['COMMENCEMENT', 'DEFERMENT'].includes(form.event_type) ? 'Course' : 'Course (optional)'}
                  <select className={selectClass} value={form.course} disabled={coursesQuery.isLoading || coursesQuery.isError} onChange={(event) => setForm({ ...form, course: event.target.value, schedule: '' })}>
                    <option value="">All eligible recipients</option>
                    {courses.filter((course) => course.is_active).map((course) => <option key={course.id} value={course.id}>{course.shortname} · {course.fullname}</option>)}
                  </select>
                  {errors.course && <span className="text-xs text-red-700">{errors.course}</span>}
                </label>
                <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">{form.event_type === 'COMMENCEMENT' ? 'Intake' : 'Intake (optional)'}
                  <select className={selectClass} value={form.schedule} disabled={!form.course || coursesQuery.isLoading} onChange={(event) => setForm({ ...form, schedule: event.target.value })}>
                    <option value="">All intakes for this course</option>
                    {availableSchedules.map((schedule) => <option key={schedule.id} value={schedule.id}>{readableDate(schedule.approximate_start_date)} to {readableDate(schedule.approximate_end_date)}</option>)}
                  </select>
                  {errors.schedule && <span className="text-xs text-red-700">{errors.schedule}</span>}
                </label>
                <Input id="calendar-start" label={form.event_type === 'MARKS_DEADLINE' ? 'Deadline date' : form.event_type === 'DEFERMENT' ? 'Original commencement date' : 'Start date'} type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} error={errors.start_date} />
                <Input id="calendar-end" label={form.event_type === 'DEFERMENT' ? 'New commencement date (blank for TBA)' : rangedTypes.has(form.event_type) ? 'End date' : 'End date (optional)'} type="date" min={form.start_date || undefined} value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} error={errors.end_date} />
                <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Audience
                  <select className={selectClass} value={form.audience} disabled={form.event_type === 'MARKS_DEADLINE' || form.event_type === 'EXAM_FEE' || form.event_type === 'COMMENCEMENT'} onChange={(event) => setForm({ ...form, audience: event.target.value as EventForm['audience'] })}>
                    <option value="STUDENTS">Students</option>
                    <option value="LECTURERS">Lecturers</option>
                    <option value="BOTH">Students and lecturers</option>
                  </select>
                  {errors.audience && <span className="text-xs text-red-700">{errors.audience}</span>}
                </label>
                <Input id="calendar-timetable" label={form.event_type === 'EXAMINATION' ? 'Timetable URL' : 'Timetable or material URL (optional)'} type="url" maxLength={500} value={form.timetable_url} onChange={(event) => setForm({ ...form, timetable_url: event.target.value })} error={errors.timetable_url} placeholder="https://..." />
              </div>
              <div className="flex justify-end border-t border-gray-100 pt-4">
                <Button type="submit" loading={publish.isPending} disabled={coursesQuery.isLoading || coursesQuery.isError || optionsQuery.isLoading}><Send className="h-4 w-4" /> Publish event</Button>
              </div>
            </form>
          </Card>

          <Card>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Published events</h2>
                <p className="text-sm text-gray-500">Previously sent calendar announcements.</p>
              </div>
              <Button type="button" size="sm" variant="ghost" onClick={() => eventsQuery.refetch()} disabled={eventsQuery.isFetching}>Refresh</Button>
            </div>
            {eventsQuery.isLoading && <div className="flex justify-center py-10"><Spinner className="text-primary" /></div>}
            {eventsQuery.isError && <p role="alert" className="py-6 text-center text-sm text-red-700">Could not load published events: {errorSummary(eventsQuery.error)}</p>}
            {!eventsQuery.isLoading && !eventsQuery.isError && events.length === 0 && <p className="py-10 text-center text-sm text-gray-500">No calendar events have been published yet.</p>}
            {events.length > 0 && <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead><tr className="border-b text-left text-xs uppercase tracking-wide text-gray-500">
                  <th className="pb-3 font-medium">Event</th><th className="pb-3 font-medium">Dates</th><th className="pb-3 font-medium">Audience</th><th className="pb-3 font-medium">Course</th><th className="pb-3 font-medium">Published</th><th className="pb-3 font-medium">Link</th>
                </tr></thead>
                <tbody className="divide-y divide-gray-100">
                  {events.map((item) => <tr key={item.id}>
                    <td className="py-3 pr-4"><p className="font-medium text-gray-900">{item.title}</p><p className="text-xs text-gray-500">{eventTypes.find((type) => type.value === item.event_type)?.label ?? item.event_type}</p></td>
                    <td className="py-3 pr-4 text-gray-600">{readableDate(item.start_date)}{item.end_date ? ` to ${readableDate(item.end_date)}` : ''}</td>
                    <td className="py-3 pr-4 text-gray-600">{item.audience === 'BOTH' ? 'Students and lecturers' : item.audience === 'LECTURERS' ? 'Lecturers' : 'Students'}</td>
                    <td className="py-3 pr-4 text-gray-600">{courses.find((course) => course.id === item.course)?.fullname ?? (item.course ? `Course #${item.course}` : 'All courses')}</td>
                    <td className="py-3 pr-4 text-gray-500">{readableDate(item.published_at)}</td>
                    <td className="py-3">{item.timetable_url && <a className="inline-flex items-center gap-1 text-primary hover:underline" href={item.timetable_url} target="_blank" rel="noopener noreferrer">Open <ExternalLink className="h-3.5 w-3.5" /></a>}</td>
                  </tr>)}
                </tbody>
              </table>
            </div>}
          </Card>
        </div>
      )}
    </AdminLayout>
  )
}
