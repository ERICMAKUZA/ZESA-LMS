'use client'

import { useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, X } from 'lucide-react'
import api, { fetchAllPages } from '@/lib/api'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Spinner from '@/components/ui/Spinner'
import { useToast } from '@/components/ui/Toast'

interface CourseTypeConfig {
  id: number
  code: string
  name: string
  is_active: boolean
  requires_qualification_assessment: boolean
  default_qualification_profile: number | null
}

interface GradeBand {
  id: number
  code: string
  label: string
  rank: number
  points: number
  is_active: boolean
}

interface QualificationProfile {
  id: number
  code: string
  name: string
  course_type: number | null
  max_o_level_sittings: number
  minimum_total_points: number
  prefer_a_level_sciences: boolean
  is_active: boolean
}

interface QualificationRequirement {
  id: number
  profile: number
  education_level: 'O_LEVEL' | 'A_LEVEL'
  subject_group: string[]
  minimum_grade_band: number
  is_required: boolean
}

type GradeForm = { code: string; label: string; rank: string; points: string }
type ProfileForm = {
  code: string
  name: string
  courseTypeId: string
  maxSittings: string
  minimumPoints: string
  preferSciences: boolean
}
type RequirementForm = {
  profileId: string
  educationLevel: 'O_LEVEL' | 'A_LEVEL'
  subjects: string
  gradeBandId: string
  isRequired: boolean
}

const emptyGrade: GradeForm = { code: '', label: '', rank: '', points: '' }
const emptyProfile: ProfileForm = {
  code: '', name: '', courseTypeId: '', maxSittings: '2', minimumPoints: '0', preferSciences: false,
}
const emptyRequirement: RequirementForm = {
  profileId: '', educationLevel: 'O_LEVEL', subjects: '', gradeBandId: '', isRequired: true,
}

const selectClass = 'w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-primary focus:ring-primary'
const actionClass = 'inline-flex items-center gap-1 rounded border border-gray-200 px-2.5 py-1.5 text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50'

function useConfiguration<T>(path: string) {
  return useQuery<T[]>({
    queryKey: ['training-config', path],
    queryFn: () => fetchAllPages<T>(`/courses/training/${path}/`, { include_inactive: 'true' }),
  })
}

function errorMessage(error: unknown): string {
  if (isAxiosError(error) && error.response?.data) {
    const data: unknown = error.response.data
    if (typeof data === 'string') return data
    if (data && typeof data === 'object') {
      const details = Object.entries(data).map(([field, value]) => {
        const message = Array.isArray(value) ? value.join(', ') : String(value)
        return field === 'detail' || field === 'non_field_errors' ? message : `${field}: ${message}`
      })
      if (details.length) return details.join(' · ')
    }
  }
  return error instanceof Error ? error.message : 'Please try again.'
}

function ErrorNotice({ error }: { error: string | null }) {
  return error && <p role="alert" className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
}

export default function QualificationSettings({ courseTypes, courseTypesError }: { courseTypes: CourseTypeConfig[]; courseTypesError: unknown }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const gradesQuery = useConfiguration<GradeBand>('grade-bands')
  const profilesQuery = useConfiguration<QualificationProfile>('qualification-profiles')
  const requirementsQuery = useConfiguration<QualificationRequirement>('qualification-requirements')
  const grades = gradesQuery.data ?? []
  const profiles = profilesQuery.data ?? []
  const requirements = requirementsQuery.data ?? []
  const activeCourseTypes = courseTypes.filter((item) => item.is_active)

  const [gradeForm, setGradeForm] = useState<GradeForm>(emptyGrade)
  const [gradeEditingId, setGradeEditingId] = useState<number | null>(null)
  const [gradeError, setGradeError] = useState<string | null>(null)
  const [profileForm, setProfileForm] = useState<ProfileForm>(emptyProfile)
  const [profileEditingId, setProfileEditingId] = useState<number | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [requirementForm, setRequirementForm] = useState<RequirementForm>(emptyRequirement)
  const [requirementEditingId, setRequirementEditingId] = useState<number | null>(null)
  const [requirementError, setRequirementError] = useState<string | null>(null)
  const [typeEditingId, setTypeEditingId] = useState<number | null>(null)
  const [typeRequiresAssessment, setTypeRequiresAssessment] = useState(false)
  const [typeProfileId, setTypeProfileId] = useState('')
  const [typeError, setTypeError] = useState<string | null>(null)

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['training-config'] })
    queryClient.invalidateQueries({ queryKey: ['course-types'] })
    queryClient.invalidateQueries({ queryKey: ['qualification-profiles'] })
  }

  const saveGrade = useMutation({
    mutationFn: async ({ id, payload }: { id: number | null; payload: Omit<GradeBand, 'id' | 'is_active'> }) => {
      const path = `/courses/training/grade-bands/${id ? `${id}/` : ''}`
      return id ? api.patch(path, payload) : api.post(path, payload)
    },
    onSuccess: () => {
      refresh()
      setGradeEditingId(null)
      setGradeForm(emptyGrade)
      setGradeError(null)
      toast({ variant: 'success', title: 'Grade band saved' })
    },
    onError: (error) => setGradeError(errorMessage(error)),
  })
  const toggleGrade = useMutation({
    mutationFn: ({ id, is_active }: GradeBand) => api.patch(`/courses/training/grade-bands/${id}/`, { is_active: !is_active }),
    onSuccess: () => { refresh(); setGradeError(null); toast({ variant: 'success', title: 'Grade band updated' }) },
    onError: (error) => setGradeError(errorMessage(error)),
  })
  const saveProfile = useMutation({
    mutationFn: async ({ id, payload }: { id: number | null; payload: Record<string, unknown> }) => {
      const path = `/courses/training/qualification-profiles/${id ? `${id}/` : ''}`
      return id ? api.patch(path, payload) : api.post(path, payload)
    },
    onSuccess: () => {
      refresh()
      setProfileEditingId(null)
      setProfileForm(emptyProfile)
      setProfileError(null)
      toast({ variant: 'success', title: 'Qualification profile saved' })
    },
    onError: (error) => setProfileError(errorMessage(error)),
  })
  const toggleProfile = useMutation({
    mutationFn: ({ id, is_active }: QualificationProfile) => api.patch(`/courses/training/qualification-profiles/${id}/`, { is_active: !is_active }),
    onSuccess: () => { refresh(); setProfileError(null); toast({ variant: 'success', title: 'Qualification profile updated' }) },
    onError: (error) => setProfileError(errorMessage(error)),
  })
  const saveRequirement = useMutation({
    mutationFn: async ({ id, payload }: { id: number | null; payload: Record<string, unknown> }) => {
      const path = `/courses/training/qualification-requirements/${id ? `${id}/` : ''}`
      return id ? api.patch(path, payload) : api.post(path, payload)
    },
    onSuccess: () => {
      refresh()
      setRequirementEditingId(null)
      setRequirementForm(emptyRequirement)
      setRequirementError(null)
      toast({ variant: 'success', title: 'Subject rule saved' })
    },
    onError: (error) => setRequirementError(errorMessage(error)),
  })
  const saveType = useMutation({
    mutationFn: ({ id, requires, profileId }: { id: number; requires: boolean; profileId: string }) => api.patch(
      `/courses/training/course-types/${id}/`,
      { requires_qualification_assessment: requires, default_qualification_profile: profileId ? Number(profileId) : null },
    ),
    onSuccess: () => {
      refresh()
      setTypeEditingId(null)
      setTypeError(null)
      toast({ variant: 'success', title: 'Course type qualification settings saved' })
    },
    onError: (error) => setTypeError(errorMessage(error)),
  })

  function submitGrade(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setGradeError(null)
    saveGrade.mutate({
      id: gradeEditingId,
      payload: {
        code: gradeForm.code.trim().toUpperCase(), label: gradeForm.label.trim(),
        rank: Number(gradeForm.rank), points: Number(gradeForm.points),
      },
    })
  }

  function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setProfileError(null)
    const payload: Record<string, unknown> = {
      code: profileForm.code.trim().toUpperCase(), name: profileForm.name.trim(),
      max_o_level_sittings: Number(profileForm.maxSittings),
      minimum_total_points: Number(profileForm.minimumPoints),
      prefer_a_level_sciences: profileForm.preferSciences,
    }
    const existing = profiles.find((item) => item.id === profileEditingId)
    if (!existing || String(existing.course_type ?? '') !== profileForm.courseTypeId) {
      payload.course_type = profileForm.courseTypeId ? Number(profileForm.courseTypeId) : null
    }
    saveProfile.mutate({ id: profileEditingId, payload })
  }

  function submitRequirement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setRequirementError(null)
    const subjectGroup = requirementForm.subjects.split(',').map((subject) => subject.trim()).filter(Boolean)
    if (!subjectGroup.length) {
      setRequirementError('Enter at least one subject.')
      return
    }
    const payload: Record<string, unknown> = {
      education_level: requirementForm.educationLevel, subject_group: subjectGroup,
      is_required: requirementForm.isRequired,
    }
    const existing = requirements.find((item) => item.id === requirementEditingId)
    if (!existing || String(existing.profile) !== requirementForm.profileId) payload.profile = Number(requirementForm.profileId)
    if (!existing || String(existing.minimum_grade_band) !== requirementForm.gradeBandId) {
      payload.minimum_grade_band = Number(requirementForm.gradeBandId)
    }
    saveRequirement.mutate({ id: requirementEditingId, payload })
  }

  const gradeName = (id: number) => grades.find((item) => item.id === id)?.label ?? 'Unknown grade'
  const profileName = (id: number) => profiles.find((item) => item.id === id)?.name ?? 'Unknown profile'
  const typeName = (id: number | null) => courseTypes.find((item) => item.id === id)?.name ?? 'All course types'

  return (
    <div className="mt-6 space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Qualification configuration</h2>
        <p className="mt-1 text-sm text-gray-500">Set grade values, assessment profiles, and the subject rules used to check applications.</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="mb-1 text-lg font-semibold text-gray-900">Grade Bands</h3>
          <p className="mb-4 text-sm text-gray-500">Higher rank means a better grade; points contribute to the total.</p>
          <ErrorNotice error={gradeError ?? (gradesQuery.isError ? `Could not load grade bands: ${errorMessage(gradesQuery.error)}` : null)} />
          <form onSubmit={submitGrade} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Input id="grade-code" label="Code" maxLength={20} required value={gradeForm.code} onChange={(event) => setGradeForm({ ...gradeForm, code: event.target.value.toUpperCase() })} />
              <Input id="grade-label" label="Label" maxLength={50} required value={gradeForm.label} onChange={(event) => setGradeForm({ ...gradeForm, label: event.target.value })} />
              <Input id="grade-rank" label="Rank" type="number" min="0" step="1" required value={gradeForm.rank} onChange={(event) => setGradeForm({ ...gradeForm, rank: event.target.value })} />
              <Input id="grade-points" label="Points" type="number" step="1" required value={gradeForm.points} onChange={(event) => setGradeForm({ ...gradeForm, points: event.target.value })} />
            </div>
            <div className="flex justify-end gap-2">
              {gradeEditingId !== null && <Button type="button" variant="ghost" onClick={() => { setGradeEditingId(null); setGradeForm(emptyGrade); setGradeError(null) }}>Cancel</Button>}
              <Button type="submit" loading={saveGrade.isPending} disabled={!gradeForm.code.trim() || !gradeForm.label.trim()}> {gradeEditingId === null ? 'Add Grade Band' : 'Save Grade Band'}</Button>
            </div>
          </form>
          <div className="mt-6 space-y-2">
            {gradesQuery.isLoading && <Spinner className="text-primary" />}
            {!gradesQuery.isLoading && !gradesQuery.isError && grades.length === 0 && <p className="text-sm text-gray-500">No grade bands yet.</p>}
            {grades.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-3 rounded-lg border border-gray-200 p-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.label} <span className="text-gray-500">({item.code})</span>{!item.is_active && <span className="ml-2 text-xs text-gray-500">Inactive</span>}</p>
                  <p className="text-xs text-gray-500">Rank {item.rank} · {item.points} points</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" className={actionClass} onClick={() => { setGradeEditingId(item.id); setGradeForm({ code: item.code, label: item.label, rank: String(item.rank), points: String(item.points) }); setGradeError(null) }}>Edit</button>
                  <button type="button" className={actionClass} disabled={toggleGrade.isPending} onClick={() => toggleGrade.mutate(item)}>{item.is_active ? <X className="h-3.5 w-3.5" /> : <Check className="h-3.5 w-3.5" />}{item.is_active ? 'Deactivate' : 'Activate'}</button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="mb-1 text-lg font-semibold text-gray-900">Qualification Profiles</h3>
          <p className="mb-4 text-sm text-gray-500">Profiles can apply to one course type or be shared by all types.</p>
          <ErrorNotice error={profileError ?? (profilesQuery.isError ? `Could not load profiles: ${errorMessage(profilesQuery.error)}` : null)} />
          <form onSubmit={submitProfile} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Input id="profile-code" label="Code" maxLength={50} required value={profileForm.code} onChange={(event) => setProfileForm({ ...profileForm, code: event.target.value.toUpperCase() })} />
              <Input id="profile-name" label="Name" maxLength={255} required value={profileForm.name} onChange={(event) => setProfileForm({ ...profileForm, name: event.target.value })} />
              <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Course type (optional)
                <select className={selectClass} value={profileForm.courseTypeId} onChange={(event) => setProfileForm({ ...profileForm, courseTypeId: event.target.value })}>
                  <option value="">All course types</option>
                  {courseTypes.filter((item) => item.is_active || String(item.id) === profileForm.courseTypeId).map((item) => <option key={item.id} value={item.id}>{item.name}{!item.is_active ? ' (inactive)' : ''}</option>)}
                </select>
              </label>
              <Input id="profile-sittings" label="Maximum O-Level sittings" type="number" min="0" step="1" required value={profileForm.maxSittings} onChange={(event) => setProfileForm({ ...profileForm, maxSittings: event.target.value })} />
              <Input id="profile-points" label="Minimum total points" type="number" min="0" step="1" required value={profileForm.minimumPoints} onChange={(event) => setProfileForm({ ...profileForm, minimumPoints: event.target.value })} />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" checked={profileForm.preferSciences} onChange={(event) => setProfileForm({ ...profileForm, preferSciences: event.target.checked })} />Prefer A-Level sciences</label>
            <div className="flex justify-end gap-2">
              {profileEditingId !== null && <Button type="button" variant="ghost" onClick={() => { setProfileEditingId(null); setProfileForm(emptyProfile); setProfileError(null) }}>Cancel</Button>}
              <Button type="submit" loading={saveProfile.isPending} disabled={!profileForm.code.trim() || !profileForm.name.trim()}> {profileEditingId === null ? 'Add Profile' : 'Save Profile'}</Button>
            </div>
          </form>
          <div className="mt-6 space-y-2">
            {profilesQuery.isLoading && <Spinner className="text-primary" />}
            {!profilesQuery.isLoading && !profilesQuery.isError && profiles.length === 0 && <p className="text-sm text-gray-500">No qualification profiles yet.</p>}
            {profiles.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-3 rounded-lg border border-gray-200 p-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.code} · {item.name}{!item.is_active && <span className="ml-2 text-xs text-gray-500">Inactive</span>}</p>
                  <p className="text-xs text-gray-500">{typeName(item.course_type)} · {item.max_o_level_sittings} O-Level sittings · {item.minimum_total_points} points{item.prefer_a_level_sciences ? ' · A-Level sciences preferred' : ''}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" className={actionClass} onClick={() => { setProfileEditingId(item.id); setProfileForm({ code: item.code, name: item.name, courseTypeId: String(item.course_type ?? ''), maxSittings: String(item.max_o_level_sittings), minimumPoints: String(item.minimum_total_points), preferSciences: item.prefer_a_level_sciences }); setProfileError(null) }}>Edit</button>
                  <button type="button" className={actionClass} disabled={toggleProfile.isPending} onClick={() => toggleProfile.mutate(item)}>{item.is_active ? <X className="h-3.5 w-3.5" /> : <Check className="h-3.5 w-3.5" />}{item.is_active ? 'Deactivate' : 'Activate'}</button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="mb-1 text-lg font-semibold text-gray-900">Subject Rules</h3>
        <p className="mb-4 text-sm text-gray-500">Separate alternative subjects with commas. Required rules must be met; optional rules do not affect eligibility.</p>
        <ErrorNotice error={requirementError ?? (requirementsQuery.isError ? `Could not load subject rules: ${errorMessage(requirementsQuery.error)}` : null)} />
        <form onSubmit={submitRequirement} className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Profile
              <select className={selectClass} required value={requirementForm.profileId} onChange={(event) => setRequirementForm({ ...requirementForm, profileId: event.target.value })}>
                <option value="">Select profile</option>
                {profiles.filter((item) => item.is_active || String(item.id) === requirementForm.profileId).map((item) => <option key={item.id} value={item.id}>{item.name}{!item.is_active ? ' (inactive)' : ''}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Education level
              <select className={selectClass} value={requirementForm.educationLevel} onChange={(event) => setRequirementForm({ ...requirementForm, educationLevel: event.target.value as RequirementForm['educationLevel'] })}>
                <option value="O_LEVEL">O-Level</option><option value="A_LEVEL">A-Level</option>
              </select>
            </label>
            <Input id="rule-subjects" label="Subjects / alternatives" required value={requirementForm.subjects} onChange={(event) => setRequirementForm({ ...requirementForm, subjects: event.target.value })} helper="Example: Mathematics, Additional Mathematics" />
            <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Minimum grade
              <select className={selectClass} required value={requirementForm.gradeBandId} onChange={(event) => setRequirementForm({ ...requirementForm, gradeBandId: event.target.value })}>
                <option value="">Select grade</option>
                {grades.filter((item) => item.is_active || String(item.id) === requirementForm.gradeBandId).map((item) => <option key={item.id} value={item.id}>{item.label}{!item.is_active ? ' (inactive)' : ''}</option>)}
              </select>
            </label>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" checked={requirementForm.isRequired} onChange={(event) => setRequirementForm({ ...requirementForm, isRequired: event.target.checked })} />Required rule</label>
          <div className="flex justify-end gap-2">
            {requirementEditingId !== null && <Button type="button" variant="ghost" onClick={() => { setRequirementEditingId(null); setRequirementForm(emptyRequirement); setRequirementError(null) }}>Cancel</Button>}
            <Button type="submit" loading={saveRequirement.isPending} disabled={!requirementForm.profileId || !requirementForm.gradeBandId || !requirementForm.subjects.trim()}>{requirementEditingId === null ? 'Add Subject Rule' : 'Save Subject Rule'}</Button>
          </div>
        </form>
        <div className="mt-6 grid gap-2 lg:grid-cols-2">
          {requirementsQuery.isLoading && <Spinner className="text-primary" />}
          {!requirementsQuery.isLoading && !requirementsQuery.isError && requirements.length === 0 && <p className="text-sm text-gray-500">No subject rules yet.</p>}
          {requirements.map((item) => (
            <div key={item.id} className="flex items-start justify-between gap-3 rounded-lg border border-gray-200 p-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{item.subject_group.join(' / ')}</p>
                <p className="text-xs text-gray-500">{profileName(item.profile)} · {item.education_level === 'O_LEVEL' ? 'O-Level' : 'A-Level'} · Minimum {gradeName(item.minimum_grade_band)} · {item.is_required ? 'Required' : 'Optional'}</p>
              </div>
              <button type="button" className={actionClass} onClick={() => { setRequirementEditingId(item.id); setRequirementForm({ profileId: String(item.profile), educationLevel: item.education_level, subjects: item.subject_group.join(', '), gradeBandId: String(item.minimum_grade_band), isRequired: item.is_required }); setRequirementError(null) }}>Edit</button>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="mb-1 text-lg font-semibold text-gray-900">Course Type Assessment</h3>
        <p className="mb-4 text-sm text-gray-500">Enable qualification assessment for an active course type and optionally choose its default profile.</p>
        <ErrorNotice error={typeError ?? (courseTypesError ? `Could not load course types: ${errorMessage(courseTypesError)}` : profilesQuery.isError ? `Could not load profiles: ${errorMessage(profilesQuery.error)}` : null)} />
        <div className="grid gap-2 lg:grid-cols-2">
          {!courseTypesError && activeCourseTypes.length === 0 && <p className="text-sm text-gray-500">No active course types.</p>}
          {activeCourseTypes.map((item) => (
            <div key={item.id} className="rounded-lg border border-gray-200 p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{item.code} · {item.name}</p>
                  <p className="text-xs text-gray-500">{item.requires_qualification_assessment ? 'Assessment required' : 'Assessment not required'} · Default: {item.default_qualification_profile ? profileName(item.default_qualification_profile) : 'None'}</p>
                </div>
                <button type="button" className={actionClass} onClick={() => { setTypeEditingId(item.id); setTypeRequiresAssessment(item.requires_qualification_assessment); setTypeProfileId(String(item.default_qualification_profile ?? '')); setTypeError(null) }}>Configure</button>
              </div>
              {typeEditingId === item.id && (
                <form className="mt-4 space-y-3 border-t border-gray-100 pt-3" onSubmit={(event) => { event.preventDefault(); setTypeError(null); saveType.mutate({ id: item.id, requires: typeRequiresAssessment, profileId: typeProfileId }) }}>
                  <label className="flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" checked={typeRequiresAssessment} onChange={(event) => setTypeRequiresAssessment(event.target.checked)} />Requires qualification assessment</label>
                  <label className="flex flex-col gap-1 text-sm font-medium text-gray-700">Default qualification profile
                    <select className={selectClass} value={typeProfileId} onChange={(event) => setTypeProfileId(event.target.value)}>
                      <option value="">No default profile</option>
                      {profiles.filter((profile) => (profile.is_active && (!profile.course_type || profile.course_type === item.id)) || String(profile.id) === typeProfileId).map((profile) => <option key={profile.id} value={profile.id}>{profile.name}{!profile.is_active ? ' (inactive)' : ''}</option>)}
                    </select>
                  </label>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="ghost" onClick={() => { setTypeEditingId(null); setTypeError(null) }}>Cancel</Button>
                    <Button type="submit" loading={saveType.isPending}>Save Settings</Button>
                  </div>
                </form>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
