'use client'

import { Suspense, useRef, useEffect, useState, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useForm, Controller, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { Upload, FileText, X, CheckCircle2 } from 'lucide-react'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import { useSubmitApplication } from '@/hooks/useApplications'
import { useCourses } from '@/hooks/useCourses'
import api from '@/lib/api'
import type { Centre } from '@/types'

// ── Validation constants ────────────────────────────────────────────────────

const MAX_FILE_SIZE = 5 * 1024 * 1024
const ACCEPTED_DOC_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png']

// ── Schema ──────────────────────────────────────────────────────────────────

const applicationSchema = z.object({
  course: z.string().min(1, 'Please select a course'),
  motivation: z.string().min(50, 'Please write at least 50 characters'),
  line_manager_email: z.string().email('Enter a valid email').optional().or(z.literal('')),
  hexco_level: z.enum(['NC', 'ND'], { required_error: 'Select NC or ND' }),
  department: z.enum(['ELECTRICAL', 'TELECOMS', 'MECHANICAL'], {
    required_error: 'Select a department',
  }),
  student_category: z.enum(['DIRECT', 'APPRENTICE', 'INTERNAL'], {
    required_error: 'Select a category',
  }),
  preferred_centre: z.string().min(1, 'Select a preferred centre'),
  is_resident: z.boolean().default(false),
  hostel_name: z.string().optional(),
  room_number: z.string().optional(),
  guardian_name: z.string().min(2, 'Guardian name required'),
  guardian_contact: z.string().min(9, 'Enter a valid phone number'),
  guardian_email: z.string().email().optional().or(z.literal('')),
  responsible_party: z.string().optional(),
  national_id_doc: z
    .custom<File>((f) => f instanceof File, 'Upload your national ID')
    .refine((f) => f.size <= MAX_FILE_SIZE, 'File must be under 5 MB')
    .refine((f) => ACCEPTED_DOC_TYPES.includes(f.type), 'PDF, JPG or PNG only'),
  academic_certs_doc: z
    .custom<File>((f) => f instanceof File, 'Upload your academic certificates')
    .refine((f) => f.size <= MAX_FILE_SIZE, 'File must be under 5 MB')
    .refine((f) => ACCEPTED_DOC_TYPES.includes(f.type), 'PDF, JPG or PNG only')
    .optional(),
  student_photo: z
    .custom<File>((f) => f instanceof File, 'Upload a passport photo')
    .refine((f) => f.size <= MAX_FILE_SIZE, 'File must be under 5 MB')
    .refine((f) => ACCEPTED_IMAGE_TYPES.includes(f.type), 'JPG or PNG only')
    .optional(),
}).refine(
  (data) => !data.is_resident || (!!data.hostel_name && data.hostel_name.length > 0),
  { message: 'Hostel name is required for residents', path: ['hostel_name'] },
)

type FormValues = z.infer<typeof applicationSchema>

// ── FileDropZone ────────────────────────────────────────────────────────────

interface FileDropZoneProps {
  label: string
  hint: string
  accept: string
  value: File | undefined
  onChange: (file: File | undefined) => void
  error?: string
  required?: boolean
}

function FileDropZone({ label, hint, accept, value, onChange, error, required }: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) onChange(file)
    },
    [onChange],
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => setIsDragging(false), [])

  const clearFile = () => {
    onChange(undefined)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-gray-700">
        {label}
        {required && <span className="ml-0.5 text-danger">*</span>}
      </label>

      {!value ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
          className={clsx(
            'flex flex-col items-center gap-2 rounded-md border-2 border-dashed px-4 py-8 cursor-pointer transition-colors',
            isDragging
              ? 'border-primary bg-primary/5'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400',
          )}
        >
          <Upload className="h-6 w-6 text-gray-400" />
          <div className="text-center">
            <p className="text-sm text-gray-600">Click to upload or drag and drop</p>
            <p className="mt-0.5 text-xs text-gray-400">{hint}</p>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3">
          <FileText className="h-5 w-5 shrink-0 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-gray-900">{value.name}</p>
            <p className="text-xs text-gray-500">{(value.size / 1024).toFixed(0)} KB</p>
          </div>
          <button
            type="button"
            onClick={clearFile}
            aria-label="Remove file"
            className="shrink-0 rounded p-0.5 text-gray-400 hover:text-danger transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onChange(file)
        }}
      />

      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  )
}

// ── Radio card ──────────────────────────────────────────────────────────────

function RadioCard({
  selected,
  onClick,
  title,
  subtitle,
}: {
  selected: boolean
  onClick: () => void
  title: string
  subtitle?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'rounded-md border-2 px-4 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        selected
          ? 'border-primary bg-primary/5'
          : 'border-gray-200 hover:border-gray-300',
      )}
    >
      <p className={clsx('text-sm font-semibold', selected ? 'text-primary' : 'text-gray-900')}>
        {title}
      </p>
      {subtitle && <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>}
    </button>
  )
}

// ── Section header ──────────────────────────────────────────────────────────

function SectionHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div>
      <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
    </div>
  )
}

// ── Main form ───────────────────────────────────────────────────────────────

const DRAFT_WATCH_FIELDS = [
  'course', 'hexco_level', 'department', 'student_category', 'preferred_centre',
  'is_resident', 'hostel_name', 'room_number', 'guardian_name', 'guardian_contact',
  'guardian_email', 'responsible_party', 'motivation', 'line_manager_email',
] as const

function NewApplicationForm() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { toast } = useToast()

  const preselectedCourse = searchParams.get('course') ?? searchParams.get('courseId') ?? ''

  const [draftId, setDraftId] = useState<string | null>(null)
  const [draftSaved, setDraftSaved] = useState(false)
  const draftTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const draftSavedTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const { data: coursesData, isLoading: coursesLoading } = useCourses()
  const { data: centresData, isLoading: centresLoading } = useQuery<Centre[]>({
    queryKey: ['centres'],
    queryFn: async () => {
      const { data } = await api.get<Centre[]>('/centres/')
      return data
    },
  })

  const courseOptions = (coursesData?.results ?? []).map((c) => ({
    value: String(c.id),
    label: c.fullname,
  }))
  const centreOptions = (centresData ?? []).map((c) => ({
    value: c.id,
    label: c.name + (c.is_primary ? ' (Primary)' : ''),
  }))

  const submitMutation = useSubmitApplication()

  const {
    control,
    register,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(applicationSchema),
    mode: 'onBlur',
    defaultValues: {
      course: preselectedCourse,
      motivation: '',
      line_manager_email: '',
      is_resident: false,
      hostel_name: '',
      room_number: '',
      guardian_name: '',
      guardian_contact: '',
      guardian_email: '',
      responsible_party: '',
      preferred_centre: '',
    },
  })

  const isResident = useWatch({ control, name: 'is_resident' }) ?? false
  const motivationValue = useWatch({ control, name: 'motivation' }) ?? ''
  const motivationLength = motivationValue.length

  // Watch non-file fields serialised to a string so the effect only fires on real changes
  const watchedJson = JSON.stringify(
    useWatch({ control, name: DRAFT_WATCH_FIELDS }),
  )

  useEffect(() => {
    if (!draftId) return
    if (draftTimer.current) clearTimeout(draftTimer.current)
    draftTimer.current = setTimeout(async () => {
      const values = getValues()
      const payload: Record<string, unknown> = {}
      DRAFT_WATCH_FIELDS.forEach((k) => {
        const val = values[k]
        if (val !== undefined) payload[k] = val
      })
      try {
        await api.patch(`/my-applications/${draftId}/`, payload)
        setDraftSaved(true)
        if (draftSavedTimer.current) clearTimeout(draftSavedTimer.current)
        draftSavedTimer.current = setTimeout(() => setDraftSaved(false), 2000)
      } catch {
        // Best-effort — no error shown to user
      }
    }, 2000)
    return () => {
      if (draftTimer.current) clearTimeout(draftTimer.current)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchedJson, draftId])

  const onSubmit = async (data: FormValues) => {
    try {
      const hasFile = data.national_id_doc || data.academic_certs_doc || data.student_photo
      let payload: FormData | Record<string, unknown>

      if (hasFile) {
        const fd = new FormData()
        Object.entries(data).forEach(([key, value]) => {
          if (value instanceof File) {
            fd.append(key, value)
          } else if (value !== undefined && value !== null) {
            fd.append(key, String(value))
          }
        })
        payload = fd
      } else {
        payload = { ...data, course: Number(data.course) } as Record<string, unknown>
      }

      const app = await submitMutation.mutateAsync(payload)
      setDraftId(app.id)
      await api.post(`/my-applications/${app.id}/submit/`)
      toast({
        variant: 'success',
        title: 'Application submitted!',
        description: 'A reviewer will assess your application and be in touch shortly.',
      })
      router.push('/applications')
    } catch (err: unknown) {
      const errData = (err as { response?: { data?: unknown } })?.response?.data
      let description = 'Please check your details and try again.'
      if (errData && typeof errData === 'object') {
        const d = errData as Record<string, unknown>
        if (typeof d.detail === 'string') {
          description = d.detail
        } else {
          const fieldMsgs = Object.entries(d)
            .map(([field, msgs]) =>
              `${field}: ${Array.isArray(msgs) ? msgs[0] : String(msgs)}`,
            )
            .join(' · ')
          if (fieldMsgs) description = fieldMsgs
        }
      }
      toast({
        variant: 'error',
        title: 'Submission failed',
        description,
      })
    }
  }

  const isLoading = coursesLoading || centresLoading

  return (
    <>
      <PageHeader
        title="Apply for Training"
        subtitle="Complete all sections — your application will be reviewed by the admissions team."
      />

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="text-primary" />
        </div>
      )}

      {!isLoading && (
        <div className="relative max-w-3xl">
          {/* Draft saved indicator */}
          <div
            style={{
              opacity: draftSaved ? 1 : 0,
              transition: 'opacity 0.3s ease',
              pointerEvents: 'none',
            }}
            className="absolute -top-8 right-0 flex items-center gap-1.5 rounded-full border border-success/20 bg-white px-3 py-1 text-xs text-success shadow-sm z-10"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            Draft saved
          </div>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-6">

            {/* ── Section 1: Programme Details ─────────────────────────── */}
            <Card header={<SectionHeader title="Programme Details" />}>
              <div className="flex flex-col gap-5 pt-1">

                {/* Course */}
                <Controller
                  control={control}
                  name="course"
                  render={({ field }) => (
                    <Select
                      label="Course *"
                      placeholder="Select a course…"
                      options={courseOptions}
                      value={field.value}
                      onValueChange={field.onChange}
                      error={errors.course?.message}
                    />
                  )}
                />

                {/* HEXCO Level */}
                <Controller
                  control={control}
                  name="hexco_level"
                  render={({ field, fieldState }) => (
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-medium text-gray-700">
                        HEXCO Level <span className="text-danger">*</span>
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        <RadioCard
                          selected={field.value === 'NC'}
                          onClick={() => field.onChange('NC')}
                          title="NC"
                          subtitle="National Certificate"
                        />
                        <RadioCard
                          selected={field.value === 'ND'}
                          onClick={() => field.onChange('ND')}
                          title="ND"
                          subtitle="National Diploma"
                        />
                      </div>
                      {fieldState.error && (
                        <p className="text-xs text-danger">{fieldState.error.message}</p>
                      )}
                    </div>
                  )}
                />

                {/* Department */}
                <Controller
                  control={control}
                  name="department"
                  render={({ field }) => (
                    <Select
                      label="Department *"
                      placeholder="Select a department…"
                      options={[
                        { value: 'ELECTRICAL', label: 'Electrical Engineering' },
                        { value: 'TELECOMS', label: 'Telecommunications' },
                        { value: 'MECHANICAL', label: 'Mechanical Engineering' },
                      ]}
                      value={field.value}
                      onValueChange={field.onChange}
                      error={errors.department?.message}
                    />
                  )}
                />

                {/* Preferred Centre */}
                <Controller
                  control={control}
                  name="preferred_centre"
                  render={({ field }) => (
                    <Select
                      label="Preferred Training Centre *"
                      placeholder="Select a centre…"
                      options={centreOptions}
                      value={field.value}
                      onValueChange={field.onChange}
                      error={errors.preferred_centre?.message}
                    />
                  )}
                />
              </div>
            </Card>

            {/* ── Section 2: About You ─────────────────────────────────── */}
            <Card header={<SectionHeader title="About You" />}>
              <div className="flex flex-col gap-5 pt-1">

                {/* Student Category */}
                <Controller
                  control={control}
                  name="student_category"
                  render={({ field, fieldState }) => (
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-medium text-gray-700">
                        Student Category <span className="text-danger">*</span>
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        <RadioCard
                          selected={field.value === 'DIRECT'}
                          onClick={() => field.onChange('DIRECT')}
                          title="Direct"
                          subtitle="Self-funded applicant"
                        />
                        <RadioCard
                          selected={field.value === 'APPRENTICE'}
                          onClick={() => field.onChange('APPRENTICE')}
                          title="Apprentice"
                          subtitle="Company-sponsored"
                        />
                        <RadioCard
                          selected={field.value === 'INTERNAL'}
                          onClick={() => field.onChange('INTERNAL')}
                          title="Internal"
                          subtitle="ZESA staff member"
                        />
                      </div>
                      {fieldState.error && (
                        <p className="text-xs text-danger">{fieldState.error.message}</p>
                      )}
                    </div>
                  )}
                />

                <Input
                  label="Line Manager / Supervisor Email"
                  type="email"
                  placeholder="manager@zesa.co.zw"
                  helper="Optional — your supervisor will be notified of this application."
                  error={errors.line_manager_email?.message}
                  {...register('line_manager_email')}
                />

                <Input
                  label="Responsible Party"
                  placeholder="Company or person responsible for fees (if sponsored)"
                  error={errors.responsible_party?.message}
                  {...register('responsible_party')}
                />
              </div>
            </Card>

            {/* ── Section 3: Accommodation ─────────────────────────────── */}
            <Card header={<SectionHeader title="Accommodation" />}>
              <div className="flex flex-col gap-4 pt-1">

                {/* Resident toggle */}
                <Controller
                  control={control}
                  name="is_resident"
                  render={({ field }) => (
                    <label className="flex w-fit cursor-pointer items-center gap-3">
                      <div
                        role="switch"
                        aria-checked={field.value}
                        tabIndex={0}
                        onClick={() => field.onChange(!field.value)}
                        onKeyDown={(e) => {
                          if (e.key === ' ' || e.key === 'Enter') {
                            e.preventDefault()
                            field.onChange(!field.value)
                          }
                        }}
                        className={clsx(
                          'relative h-6 w-11 cursor-pointer rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
                          field.value ? 'bg-primary' : 'bg-gray-300',
                        )}
                      >
                        <div
                          className={clsx(
                            'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
                            field.value ? 'translate-x-5' : 'translate-x-0.5',
                          )}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700">
                        I will be residing in ZNTC hostel
                      </span>
                    </label>
                  )}
                />

                {/* Hostel fields — animate in/out via max-height */}
                <div
                  style={{
                    maxHeight: isResident ? '160px' : '0',
                    overflow: 'hidden',
                    transition: 'max-height 0.25s ease',
                  }}
                >
                  <div className="grid grid-cols-2 gap-4 pt-1">
                    <Input
                      label="Hostel Name *"
                      placeholder="e.g. Block A"
                      error={errors.hostel_name?.message}
                      {...register('hostel_name')}
                    />
                    <Input
                      label="Room Number"
                      placeholder="e.g. 14"
                      error={errors.room_number?.message}
                      {...register('room_number')}
                    />
                  </div>
                </div>
              </div>
            </Card>

            {/* ── Section 4: Guardian / Next of Kin ───────────────────── */}
            <Card
              header={
                <SectionHeader
                  title="Guardian / Next of Kin"
                  description="We will contact this person in case of emergency."
                />
              }
            >
              <div className="flex flex-col gap-4 pt-1">
                <Input
                  label="Full Name *"
                  placeholder="Guardian's full name"
                  error={errors.guardian_name?.message}
                  {...register('guardian_name')}
                />
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Phone Number *"
                    type="tel"
                    placeholder="+263 7X XXX XXXX"
                    error={errors.guardian_contact?.message}
                    {...register('guardian_contact')}
                  />
                  <Input
                    label="Email Address"
                    type="email"
                    placeholder="guardian@example.com"
                    error={errors.guardian_email?.message}
                    {...register('guardian_email')}
                  />
                </div>
              </div>
            </Card>

            {/* ── Section 5: Motivation ────────────────────────────────── */}
            <Card header={<SectionHeader title="Motivation" />}>
              <div className="flex flex-col gap-1.5 pt-1">
                <div className="flex items-baseline justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    Statement of Motivation <span className="text-danger">*</span>
                  </label>
                  <span
                    className={clsx(
                      'text-xs tabular-nums transition-colors',
                      motivationLength >= 50 ? 'text-gray-400' : 'text-warning',
                    )}
                  >
                    {motivationLength} / 50 minimum
                  </span>
                </div>
                <textarea
                  rows={6}
                  placeholder="Explain why you want to enrol in this programme and how it relates to your career goals…"
                  className="block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-primary focus:ring-primary"
                  {...register('motivation')}
                />
                {errors.motivation && (
                  <p className="text-xs text-danger">{errors.motivation.message}</p>
                )}
              </div>
            </Card>

            {/* ── Section 6: Supporting Documents ─────────────────────── */}
            <Card
              header={
                <SectionHeader
                  title="Supporting Documents"
                  description="Files must be PDF, JPG, or PNG and no larger than 5 MB each."
                />
              }
            >
              <div className="flex flex-col gap-6 pt-1">
                <Controller
                  control={control}
                  name="national_id_doc"
                  render={({ field, fieldState }) => (
                    <FileDropZone
                      label="National ID / Passport"
                      hint="PDF, JPG, or PNG — max 5 MB"
                      accept=".pdf,.jpg,.jpeg,.png"
                      value={field.value as File | undefined}
                      onChange={field.onChange}
                      error={fieldState.error?.message}
                      required
                    />
                  )}
                />

                <Controller
                  control={control}
                  name="academic_certs_doc"
                  render={({ field, fieldState }) => (
                    <FileDropZone
                      label="Academic Certificates"
                      hint="PDF, JPG, or PNG — max 5 MB (optional)"
                      accept=".pdf,.jpg,.jpeg,.png"
                      value={field.value as File | undefined}
                      onChange={field.onChange}
                      error={fieldState.error?.message}
                    />
                  )}
                />

                <Controller
                  control={control}
                  name="student_photo"
                  render={({ field, fieldState }) => (
                    <FileDropZone
                      label="Passport Photo"
                      hint="JPG or PNG — max 5 MB, square crop recommended (optional)"
                      accept=".jpg,.jpeg,.png"
                      value={field.value as File | undefined}
                      onChange={field.onChange}
                      error={fieldState.error?.message}
                    />
                  )}
                />
              </div>
            </Card>

            {/* ── Submit ───────────────────────────────────────────────── */}
            <Button
              type="submit"
              size="lg"
              className="w-full"
              loading={isSubmitting || submitMutation.isPending}
            >
              Submit Application
            </Button>
          </form>
        </div>
      )}
    </>
  )
}

// ── Page wrapper ────────────────────────────────────────────────────────────

export default function NewApplicationPage() {
  return (
    <StudentLayout>
      <Suspense
        fallback={
          <div className="flex justify-center py-16">
            <Spinner className="text-primary" />
          </div>
        }
      >
        <NewApplicationForm />
      </Suspense>
    </StudentLayout>
  )
}
