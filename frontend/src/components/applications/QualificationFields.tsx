'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api, { fetchAllPages } from '@/lib/api'

export interface AcademicResultInput {
  subject: string
  grade_band_id: number
}

export interface AcademicSittingInput {
  education_level: 'O_LEVEL' | 'A_LEVEL'
  sitting_number: number
  exam_year: number
  exam_session: string
  results: AcademicResultInput[]
}

interface TaxonomyItem { id: number; code: string; name: string }
interface GradeBand { id: number; code: string; label: string; points: number; rank: number }
export interface TrainingCourse {
  id: number
  fullname: string
  course_type: (TaxonomyItem & { requires_qualification_assessment?: boolean }) | null
  departments: TaxonomyItem[]
  certification_types: TaxonomyItem[]
  qualification_profile_id: number | null
  qualification_assessment_enabled: boolean
  max_o_level_sittings: number | null
  minimum_points_required: number | null
  required_subjects: string[]
}

export interface QualificationSelection {
  course: string
  selected_department_id: string
  certification_type_id: string
  academic_sittings: AcademicSittingInput[]
}

export const emptySelection: QualificationSelection = {
  course: '', selected_department_id: '', certification_type_id: '', academic_sittings: [],
}

export function validateQualificationSelection(selection: QualificationSelection, course?: TrainingCourse): string | null {
  if (!course) return 'Select a course.'
  if (course.departments.length > 1 && !selection.selected_department_id) return 'Select a department for this course.'
  if (course.certification_types.length > 0 && !selection.certification_type_id) return 'Select a certification type.'
  if (course.qualification_assessment_enabled && !selection.academic_sittings.some(
    sitting => sitting.education_level === 'O_LEVEL' && sitting.results.some(result => result.subject.trim() && result.grade_band_id),
  )) return 'Enter at least one O-Level subject and grade.'
  for (const sitting of selection.academic_sittings) {
    if (!sitting.exam_year || sitting.results.length === 0 || sitting.results.some(result => !result.subject.trim() || !result.grade_band_id)) {
      return 'Complete every academic sitting, subject, and grade, or remove incomplete entries.'
    }
  }
  return null
}

interface Props {
  value: QualificationSelection
  onChange: (next: QualificationSelection) => void
  error?: string | null
  lockCourse?: boolean
}

const selectClass = 'w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'

export default function QualificationFields({ value, onChange, error, lockCourse = false }: Props) {
  const { data: courses = [], isLoading: coursesLoading } = useQuery<TrainingCourse[]>({
    queryKey: ['training-selection'],
    queryFn: () => api.get<TrainingCourse[]>('/courses/training/selection/').then(response => response.data),
  })
  const { data: grades = [], isLoading: gradesLoading } = useQuery<GradeBand[]>({
    queryKey: ['active-grade-bands'],
    queryFn: () => fetchAllPages<GradeBand>('/courses/training/grade-bands/'),
  })

  const course = courses.find(item => String(item.id) === value.course)
  const departments = Array.from(new Map((lockCourse && course ? course.departments : courses.flatMap(item => item.departments)).map(item => [item.id, item])).values())
    .sort((a, b) => a.name.localeCompare(b.name))
  const visibleCourses = value.selected_department_id
    ? courses.filter(item => item.departments.length === 0 || item.departments.some(dept => String(dept.id) === value.selected_department_id))
    : courses

  useEffect(() => {
    if (!course) return
    const nextDepartment = course.departments.length === 1
      ? String(course.departments[0].id)
      : course.departments.some(item => String(item.id) === value.selected_department_id)
        ? value.selected_department_id : ''
    const nextCertification = course.certification_types.length === 1
      ? String(course.certification_types[0].id)
      : course.certification_types.some(item => String(item.id) === value.certification_type_id)
        ? value.certification_type_id : ''
    if (nextDepartment !== value.selected_department_id || nextCertification !== value.certification_type_id) {
      onChange({ ...value, selected_department_id: nextDepartment, certification_type_id: nextCertification })
    }
  }, [course, value, onChange])

  const updateSitting = (index: number, patch: Partial<AcademicSittingInput>) => {
    const sittings = value.academic_sittings.map((sitting, i) => i === index ? { ...sitting, ...patch } : sitting)
    onChange({ ...value, academic_sittings: sittings })
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-medium text-gray-700">
          Department <span className="font-normal text-gray-500">(optional first step)</span>
          <select className={`${selectClass} mt-1.5`} value={value.selected_department_id} onChange={event => {
            const department = event.target.value
            onChange({ ...value, selected_department_id: department,
              course: course && department && course.departments.length > 0 && !course.departments.some(item => String(item.id) === department) ? '' : value.course,
              certification_type_id: course && department && course.departments.length > 0 && !course.departments.some(item => String(item.id) === department) ? '' : value.certification_type_id,
            })
          }}>
            <option value="">All departments</option>
            {departments.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <label className="block text-sm font-medium text-gray-700">
          Course <span className="text-danger">*</span>
          <select className={`${selectClass} mt-1.5`} value={value.course} disabled={coursesLoading || lockCourse} onChange={event => {
            onChange({ ...value, course: event.target.value, certification_type_id: '', academic_sittings: [] })
          }}>
            <option value="">{coursesLoading ? 'Loading courses...' : 'Select a course'}</option>
            {visibleCourses.map(item => <option key={item.id} value={item.id}>{item.fullname}</option>)}
          </select>
        </label>
      </div>
      {course && (
        <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
          {course.course_type?.name && <span className="font-medium">{course.course_type.name}</span>}
          {course.minimum_points_required != null && <span> · Minimum {course.minimum_points_required} points</span>}
          {course.required_subjects.length > 0 && <p className="mt-1">Required subjects: {course.required_subjects.join(', ')}</p>}
        </div>
      )}
      {course && course.certification_types.length > 0 && (
        <label className="block text-sm font-medium text-gray-700">
          Certification <span className="text-danger">*</span>
          <select className={`${selectClass} mt-1.5`} value={value.certification_type_id} onChange={event => onChange({ ...value, certification_type_id: event.target.value })}>
            <option value="">Select certification</option>
            {course.certification_types.map(item => <option key={item.id} value={item.id}>{item.code} - {item.name}</option>)}
          </select>
        </label>
      )}
      {course && (
        <section className="space-y-4 border-t border-gray-200 pt-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Academic results {course.qualification_assessment_enabled ? '*' : '(optional)'}</h3>
            <p className="text-xs text-gray-500">Enter the grades shown on your certificates. The reviewer will see an automatic assessment, but can make the final decision.</p>
          </div>
          {value.academic_sittings.map((sitting, index) => (
            <div key={`${sitting.education_level}-${sitting.sitting_number}-${index}`} className="space-y-3 rounded-md border border-gray-200 p-4">
              <div className="flex items-center justify-between gap-3">
                <strong className="text-sm">{sitting.education_level === 'O_LEVEL' ? 'O-Level' : 'A-Level'} sitting {sitting.sitting_number}</strong>
                <button type="button" className="text-xs text-danger" onClick={() => onChange({ ...value, academic_sittings: value.academic_sittings.filter((_, i) => i !== index) })}>Remove sitting</button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-xs text-gray-700">Exam year
                  <input className={`${selectClass} mt-1`} type="number" min="1950" max="2100" value={sitting.exam_year} onChange={event => updateSitting(index, { exam_year: Number(event.target.value) })} />
                </label>
                <label className="text-xs text-gray-700">Session (optional)
                  <input className={`${selectClass} mt-1`} value={sitting.exam_session} onChange={event => updateSitting(index, { exam_session: event.target.value })} placeholder="June or November" />
                </label>
              </div>
              {sitting.results.map((result, resultIndex) => (
                <div key={resultIndex} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
                  <label className="text-xs text-gray-700">Subject
                    <input className={`${selectClass} mt-1`} value={result.subject} onChange={event => updateSitting(index, { results: sitting.results.map((entry, i) => i === resultIndex ? { ...entry, subject: event.target.value } : entry) })} placeholder="Mathematics" />
                  </label>
                  <label className="text-xs text-gray-700">Grade
                    <select className={`${selectClass} mt-1`} disabled={gradesLoading} value={result.grade_band_id || ''} onChange={event => updateSitting(index, { results: sitting.results.map((entry, i) => i === resultIndex ? { ...entry, grade_band_id: Number(event.target.value) } : entry) })}>
                      <option value="">Select grade</option>
                      {grades.map(grade => <option key={grade.id} value={grade.id}>{grade.label} ({grade.points} points)</option>)}
                    </select>
                  </label>
                  <button type="button" className="rounded px-2 py-2 text-xs text-danger" aria-label="Remove subject" onClick={() => updateSitting(index, { results: sitting.results.filter((_, i) => i !== resultIndex) })}>Remove</button>
                </div>
              ))}
              <button type="button" className="text-xs font-medium text-primary" onClick={() => updateSitting(index, { results: [...sitting.results, { subject: '', grade_band_id: 0 }] })}>+ Add subject</button>
            </div>
          ))}
          <div className="flex flex-wrap gap-3">
            {(['O_LEVEL', 'A_LEVEL'] as const).map(level => (
              <button key={level} type="button" disabled={level === 'O_LEVEL' && Boolean(course.max_o_level_sittings && value.academic_sittings.filter(item => item.education_level === 'O_LEVEL').length >= course.max_o_level_sittings)} className="rounded-md border border-primary px-3 py-2 text-xs font-medium text-primary hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-40" onClick={() => {
                const existing = value.academic_sittings.filter(item => item.education_level === level)
                if (level === 'O_LEVEL' && course.max_o_level_sittings && existing.length >= course.max_o_level_sittings) return
                onChange({ ...value, academic_sittings: [...value.academic_sittings, {
                  education_level: level, sitting_number: Math.max(0, ...existing.map(item => item.sitting_number)) + 1, exam_year: new Date().getFullYear(), exam_session: '',
                  results: [{ subject: '', grade_band_id: 0 }],
                }] })
              }}>+ Add {level === 'O_LEVEL' ? 'O-Level' : 'A-Level'} sitting</button>
            ))}
          </div>
          {course.max_o_level_sittings && <p className="text-xs text-gray-500">Maximum O-Level sittings: {course.max_o_level_sittings}</p>}
        </section>
      )}
      {error && <p role="alert" className="text-xs text-danger">{error}</p>}
    </div>
  )
}
