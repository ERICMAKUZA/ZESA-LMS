'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'
import api, { fetchAllPages } from '@/lib/api'
import type {
  CertificationType,
  Course,
  CourseCategory,
  CourseType,
  Department,
  QualificationProfile,
  User,
} from '@/types'

const months = [
  { value: '1', label: 'January' },
  { value: '2', label: 'February' },
  { value: '3', label: 'March' },
  { value: '4', label: 'April' },
  { value: '5', label: 'May' },
  { value: '6', label: 'June' },
  { value: '7', label: 'July' },
  { value: '8', label: 'August' },
  { value: '9', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
]

const weeks = [
  { value: '1', label: 'Week 1' },
  { value: '2', label: 'Week 2' },
  { value: '3', label: 'Week 3' },
  { value: '4', label: 'Week 4' },
]

interface CourseEditorProps {
  course?: Course
}

function parseSubjects(raw: string): string[] {
  return raw
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function matchesSearch(text: string, search: string) {
  if (!search.trim()) return true
  const compare = text.toLowerCase()
  return compare.includes(search.toLowerCase())
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
    price: course?.price ?? '',
    maxCapacity: course?.max_capacity ? String(course.max_capacity) : '',
    thumbnailUrl: course?.thumbnail_url ?? '',
    isActive: course?.is_active ?? true,
    requiresApproval: course?.requires_approval ?? true,
    intakeYear: String(new Date().getFullYear()),
    intakeMonth: '',
    intakeWeek: '',
    intakeCapacity: course?.max_capacity ? String(course.max_capacity) : '',
    intakePaymentDueDate: '',
    intakeNotes: '',
    courseTypeId: course?.course_type?.id ? String(course.course_type.id) : '',
    departmentIds: course?.departments?.map((department) => String(department.id)) ?? [],
    certificationTypeIds: course?.certification_types?.map((cert) => String(cert.id)) ?? [],
    minimumPointsRequired: course?.minimum_points_required != null ? String(course.minimum_points_required) : '',
    requiredSubjects: (course?.required_subjects ?? []).join(', '),
    assessmentEnabled: course?.qualification_assessment_enabled ?? course?.course_type?.requires_qualification_assessment ?? false,
    qualificationProfileId: course?.qualification_profile?.id
      ? String(course.qualification_profile.id)
      : course?.course_type?.default_qualification_profile ? String(course.course_type.default_qualification_profile) : '',
  })
  const [departmentSearch, setDepartmentSearch] = useState('')
  const [certificationSearch, setCertificationSearch] = useState('')

  const [assignmentError, setAssignmentError] = useState('')
  const [intakeError, setIntakeError] = useState('')

  const categoriesQuery = useQuery<CourseCategory[]>({
    queryKey: ['course-categories'],
    queryFn: () => fetchAllPages<CourseCategory>('/courses/categories/'),
  })
  const courseTypesQuery = useQuery<CourseType[]>({
    queryKey: ['course-types'],
    queryFn: () => fetchAllPages<CourseType>('/courses/training/course-types/', { include_inactive: 'true' }),
  })
  const departmentsQuery = useQuery<Department[]>({
    queryKey: ['course-departments'],
    queryFn: () => fetchAllPages<Department>('/courses/training/departments/', { include_inactive: 'true' }),
  })
  const certTypesQuery = useQuery<CertificationType[]>({
    queryKey: ['course-cert-types'],
    queryFn: () => fetchAllPages<CertificationType>('/courses/training/certification-types/', { include_inactive: 'true' }),
  })
  const profilesQuery = useQuery<QualificationProfile[]>({
    queryKey: ['qualification-profiles'],
    queryFn: () => fetchAllPages<QualificationProfile>('/courses/training/qualification-profiles/', { include_inactive: 'true' }),
  })
  const lecturersQuery = useQuery<User[]>({
    queryKey: ['active-lecturers'],
    queryFn: async () => (await api.get('/admin/lecturers/')).data,
  })

  const courseTypes = courseTypesQuery.data ?? []
  const departments = departmentsQuery.data ?? []
  const certTypes = certTypesQuery.data ?? []
  const profiles = profilesQuery.data ?? []
  const lecturers = lecturersQuery.data ?? []
  const selectedCourseTypeId = Number(form.courseTypeId)
  const availableCourseTypes = courseTypes.filter(
    (courseType) => courseType.is_active || courseType.id === selectedCourseTypeId,
  )

  const filteredDepartments = useMemo(
    () => departments.filter((department) => (
      (department.is_active || form.departmentIds.includes(String(department.id)))
      && matchesSearch(`${department.code} ${department.name}`, departmentSearch)
    )),
    [departments, departmentSearch, form.departmentIds],
  )

  const relatedCertificationTypes = useMemo(() => {
    if (!form.courseTypeId) {
      return []
    }

    const target = Number(form.courseTypeId)
    return certTypes.filter((certType) => (
      certType.course_type === target
      && (certType.is_active || form.certificationTypeIds.includes(String(certType.id)))
    ))
  }, [certTypes, form.certificationTypeIds, form.courseTypeId])

  const filteredCertificationTypes = useMemo(
    () => relatedCertificationTypes.filter((certType) => matchesSearch(`${certType.code} ${certType.name}`, certificationSearch)),
    [relatedCertificationTypes, certificationSearch],
  )

  const saveCourse = useMutation({
    mutationFn: async () => {
      const payload = {
        shortname: form.shortname.trim(),
        fullname: form.fullname.trim(),
        summary: form.summary.trim(),
        category_id: Number(form.categoryId),
        duration_days: form.durationDays ? Number(form.durationDays) : null,
        price: form.price ? Number(form.price) : null,
        max_capacity: form.maxCapacity ? Number(form.maxCapacity) : null,
        thumbnail_url: form.thumbnailUrl.trim(),
        is_active: form.isActive,
        requires_approval: form.requiresApproval,
        course_type_id: form.courseTypeId ? Number(form.courseTypeId) : null,
        department_ids: form.departmentIds.map(Number),
        certification_type_ids: form.certificationTypeIds.map(Number),
        minimum_points_required: form.minimumPointsRequired === ''
          ? null
          : Number(form.minimumPointsRequired),
        required_subjects: parseSubjects(form.requiredSubjects),
        qualification_assessment_enabled: form.assessmentEnabled,
        qualification_profile_id: form.qualificationProfileId ? Number(form.qualificationProfileId) : null,
        lecturer_ids: lecturerIds,
        ...(!course && {
          initial_schedule: {
            year: Number(form.intakeYear),
            month: Number(form.intakeMonth),
            week_in_month: Number(form.intakeWeek),
            max_capacity: Number(form.intakeCapacity || form.maxCapacity),
            payment_due_date: form.intakePaymentDueDate || null,
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

  const [lecturerIds, setLecturerIds] = useState<number[]>(course?.lecturers.map((lecturer) => lecturer.id) ?? [])

  const setField = <T extends keyof typeof form>(field: T, value: typeof form[T]) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const setCourseType = (value: string) => {
    const nextType = courseTypes.find((item) => String(item.id) === value)
    setForm((current) => ({
      ...current,
      courseTypeId: value,
      assessmentEnabled: nextType?.requires_qualification_assessment ?? false,
      certificationTypeIds: [],
      qualificationProfileId: nextType?.default_qualification_profile ? String(nextType.default_qualification_profile) : '',
    }))
  }

  const availableProfiles = profiles.filter((profile) => profile.is_active && (!profile.course_type || profile.course_type === selectedCourseTypeId))

  const toggleDepartment = (departmentId: number) => {
    setForm((current) => ({
      ...current,
      departmentIds: current.departmentIds.includes(String(departmentId))
        ? current.departmentIds.filter((id) => id !== String(departmentId))
        : [...current.departmentIds, String(departmentId)],
    }))
  }

  const toggleCertificationType = (certId: number) => {
    setForm((current) => ({
      ...current,
      certificationTypeIds: current.certificationTypeIds.includes(String(certId))
        ? current.certificationTypeIds.filter((id) => id !== String(certId))
        : [...current.certificationTypeIds, String(certId)],
    }))
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

    if (!form.categoryId) {
      setAssignmentError('Select a category before saving this course.')
      return
    }

    if (!form.courseTypeId) {
      setAssignmentError('Select a course type before saving this course.')
      return
    }

    if (lecturerIds.length === 0) {
      setAssignmentError('Assign at least one lecturer before saving this course.')
      return
    }

    if (form.assessmentEnabled && !form.qualificationProfileId) {
      setAssignmentError('Choose a qualification profile for courses that assess academic results.')
      return
    }

    if (!course && (!form.intakeYear || !form.intakeMonth || !form.intakeWeek || !(form.intakeCapacity || form.maxCapacity))) {
      setIntakeError('Add the date and capacity for the first course intake.')
      return
    }

    setAssignmentError('')
    setIntakeError('')
    saveCourse.mutate()
  }

  const isLoading = categoriesQuery.isLoading
    || courseTypesQuery.isLoading
    || departmentsQuery.isLoading
    || certTypesQuery.isLoading
    || lecturersQuery.isLoading

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
            <Select
              label="Category *"
              value={form.categoryId}
              onValueChange={(value) => setField('categoryId', value)}
              options={categoriesQuery.data?.map((category) => ({ value: String(category.id), label: category.name })) ?? []}
              placeholder="Select a category"
            />
            <Select
              label="Course type *"
              value={form.courseTypeId}
              onValueChange={(value) => setCourseType(value)}
              options={availableCourseTypes.map((courseType) => ({
                value: String(courseType.id),
                label: `${courseType.code} — ${courseType.name}${courseType.is_active ? '' : ' (inactive)'}`,
              }))}
              placeholder="Select a course type"
            />
            <Input label="Duration (days)" type="number" min="1" value={form.durationDays} onChange={(event) => setField('durationDays', event.target.value)} />
            <Input label="Fee (USD)" type="number" min="0" step="0.01" value={form.price} onChange={(event) => setField('price', event.target.value)} />
            <Input label="Maximum class size" type="number" min="1" value={form.maxCapacity} onChange={(event) => setField('maxCapacity', event.target.value)} />
            <Input label="Minimum points to qualify" type="number" min="0" disabled={!form.assessmentEnabled} value={form.minimumPointsRequired} onChange={(event) => setField('minimumPointsRequired', event.target.value)} helper={!form.assessmentEnabled ? 'Enable assessment to apply a points threshold.' : undefined} />
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <input type="checkbox" checked={form.assessmentEnabled} onChange={(event) => setField('assessmentEnabled', event.target.checked)} className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary" />
              Assess points and required subjects for this course
            </label>
            {form.assessmentEnabled && (
              <Select
                label="Qualification profile *"
                value={form.qualificationProfileId}
                onValueChange={(value) => setField('qualificationProfileId', value)}
                options={availableProfiles.map((profile) => ({ value: String(profile.id), label: `${profile.name} · ${profile.minimum_total_points} points` }))}
                placeholder="Select a qualification profile"
              />
            )}
            <Input label="Course image URL" type="url" value={form.thumbnailUrl} onChange={(event) => setField('thumbnailUrl', event.target.value)} />
            <div className="md:col-span-2 flex flex-col gap-1">
              <label htmlFor="required-subjects" className="text-sm font-medium text-gray-700">Required subjects</label>
              <textarea
                id="required-subjects"
                rows={3}
                value={form.requiredSubjects}
                disabled={!form.assessmentEnabled}
                onChange={(event) => setField('requiredSubjects', event.target.value)}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Maths, English, Physics"
              />
              <span className="text-xs text-gray-500">Use commas or new lines. Leave empty when no fixed subject requirement applies.</span>
            </div>
            <div className="md:col-span-2 flex flex-col gap-1">
              <label htmlFor="course-summary" className="text-sm font-medium text-gray-700">Course description</label>
              <textarea
                id="course-summary"
                rows={5}
                value={form.summary}
                onChange={(event) => setField('summary', event.target.value)}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>
        )}
      </Card>

      <Card>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Departments (optional)</h2>
            <p className="mt-1 text-sm text-gray-500">Select one or more departments linked to this course.</p>
          </div>
          <Input
            placeholder="Search departments"
            value={departmentSearch}
            onChange={(event) => setDepartmentSearch(event.target.value)}
            className="max-w-xs"
          />
        </div>
        {!isLoading && filteredDepartments.length === 0 && (
          <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">No departments match your filter.</p>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          {filteredDepartments.map((department) => {
            const selected = form.departmentIds.includes(String(department.id))
            return (
              <label key={department.id} className={`flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors ${selected ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-primary/50'}`}>
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => toggleDepartment(department.id)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span>
                  <span className="block font-medium text-gray-900">{department.name}</span>
                  <span className="block text-sm text-gray-500">{department.code}</span>
                </span>
              </label>
            )
          })}
        </div>
      </Card>

      <Card>
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Certification Types</h2>
            <p className="mt-1 text-sm text-gray-500">Only types linked to the selected course type are available.</p>
          </div>
          <Input
            placeholder="Search certifications"
            value={certificationSearch}
            onChange={(event) => setCertificationSearch(event.target.value)}
            className="max-w-xs"
          />
        </div>

        {filteredCertificationTypes.length === 0 && (
          <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">No certification options match the selected course type.</p>
        )}

        <div className="grid gap-3 sm:grid-cols-2">
          {filteredCertificationTypes.map((certType) => {
            const selected = form.certificationTypeIds.includes(String(certType.id))
            return (
              <label key={certType.id} className={`flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors ${selected ? 'border-primary bg-primary/5' : 'border-gray-200 hover:border-primary/50'}`}>
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => toggleCertificationType(certType.id)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <span>
                  <span className="block font-medium text-gray-900">{certType.name}</span>
                  <span className="block text-sm text-gray-500">{certType.code}</span>
                </span>
              </label>
            )
          })}
        </div>
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
            <Input label="Fee payment deadline" type="date" value={form.intakePaymentDueDate} onChange={(event) => setField('intakePaymentDueDate', event.target.value)} helper="Optional. If blank, acceptance messages use the intake start date." />
            <div className="md:col-span-2 lg:col-span-4 flex flex-col gap-1">
              <label htmlFor="intake-notes" className="text-sm font-medium text-gray-700">Intake notes</label>
              <textarea
                id="intake-notes"
                rows={3}
                value={form.intakeNotes}
                onChange={(event) => setField('intakeNotes', event.target.value)}
                className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Optional location, equipment, or preparation notes."
              />
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
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => toggleLecturer(lecturer.id)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
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
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.isActive}
                onChange={(event) => setField('isActive', event.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              Publish this course
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.requiresApproval}
                onChange={(event) => setField('requiresApproval', event.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              Require application approval before enrolment
            </label>
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
