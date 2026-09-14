'use client'

import { useMemo, useState } from 'react'
import { Check, X } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import AdminLayout from '@/components/layout/AdminLayout'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import PageHeader from '@/components/ui/PageHeader'
import Spinner from '@/components/ui/Spinner'
import QualificationSettings from '@/components/admin/QualificationSettings'
import api, { fetchAllPages } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import type { CertificationType, CourseType, Department } from '@/types'

function matchesSearch(text: string, search: string) {
  if (!search.trim()) return true
  return text.toLowerCase().includes(search.toLowerCase())
}

function useTrainingConfig<T>(path: string) {
  return useQuery<T[]>({
    queryKey: ['training-config', path],
    queryFn: () => fetchAllPages<T>(`/courses/training/${path}/`, { include_inactive: 'true' }),
  })
}

export default function AdminSettingsPage() {
  const [departmentSearch, setDepartmentSearch] = useState('')
  const [typeSearch, setTypeSearch] = useState('')
  const [certSearch, setCertSearch] = useState('')
  const [departmentForm, setDepartmentForm] = useState({
    code: '',
    name: '',
    description: '',
  })
  const [typeForm, setTypeForm] = useState({
    code: '',
    name: '',
    description: '',
  })
  const [certForm, setCertForm] = useState({
    courseTypeId: '',
    code: '',
    name: '',
    description: '',
  })

  const { toast } = useToast()
  const queryClient = useQueryClient()

  const departmentsQuery = useTrainingConfig<Department>('departments')
  const courseTypesQuery = useTrainingConfig<CourseType>('course-types')
  const certificationTypesQuery = useTrainingConfig<CertificationType>('certification-types')

  const departments = departmentsQuery.data ?? []
  const courseTypes = courseTypesQuery.data ?? []
  const activeCourseTypes = courseTypes.filter((item) => item.is_active)
  const certificationTypes = certificationTypesQuery.data ?? []

  const filteredDepartments = useMemo(
    () => departments.filter((item) => matchesSearch(`${item.code} ${item.name} ${item.description}`, departmentSearch)),
    [departments, departmentSearch],
  )
  const filteredCourseTypes = useMemo(
    () => courseTypes.filter((item) => matchesSearch(`${item.code} ${item.name} ${item.description}`, typeSearch)),
    [courseTypes, typeSearch],
  )

  const courseTypeNameById = useMemo(() => {
    const map = new Map<number, string>()
    for (const item of courseTypes) {
      map.set(item.id, item.name)
    }
    return map
  }, [courseTypes])

  const filteredCertifications = useMemo(
    () => certificationTypes.filter((item) => matchesSearch(
      `${item.code} ${item.name} ${item.description} ${(courseTypeNameById.get(item.course_type) ?? '')}`,
      certSearch,
    )),
    [certificationTypes, certSearch, courseTypeNameById],
  )

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['training-config'] })
  }

  const createDepartment = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/courses/training/departments/', {
        ...departmentForm,
      })
      return data
    },
    onSuccess: () => {
      invalidateAll()
      setDepartmentForm({ code: '', name: '', description: '' })
      toast({ variant: 'success', title: 'Department created' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Could not create department' })
    },
  })

  const createCourseType = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/courses/training/course-types/', {
        ...typeForm,
      })
      return data
    },
    onSuccess: () => {
      invalidateAll()
      setTypeForm({ code: '', name: '', description: '' })
      toast({ variant: 'success', title: 'Course type created' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Could not create course type' })
    },
  })

  const createCertificationType = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/courses/training/certification-types/', {
        ...certForm,
        course_type: Number(certForm.courseTypeId),
      })
      return data
    },
    onSuccess: () => {
      invalidateAll()
      setCertForm({ courseTypeId: '', code: '', name: '', description: '' })
      toast({ variant: 'success', title: 'Certification type created' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Could not create certification type' })
    },
  })

  const toggleDepartment = useMutation({
    mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) => {
      const { data } = await api.patch(`/courses/training/departments/${id}/`, { is_active: !is_active })
      return data
    },
    onSuccess: () => {
      invalidateAll()
      toast({ variant: 'success', title: 'Department updated' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Could not update department' })
    },
  })

  const toggleCourseType = useMutation({
    mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) => {
      const { data } = await api.patch(`/courses/training/course-types/${id}/`, { is_active: !is_active })
      return data
    },
    onSuccess: () => {
      invalidateAll()
      toast({ variant: 'success', title: 'Course type updated' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Could not update course type' })
    },
  })

  const toggleCertificationType = useMutation({
    mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) => {
      const { data } = await api.patch(`/courses/training/certification-types/${id}/`, { is_active: !is_active })
      return data
    },
    onSuccess: () => {
      invalidateAll()
      toast({ variant: 'success', title: 'Certification type updated' })
    },
    onError: () => {
      toast({ variant: 'error', title: 'Could not update certification type' })
    },
  })

  const isLoading = departmentsQuery.isLoading || courseTypesQuery.isLoading || certificationTypesQuery.isLoading

  if (isLoading) {
    return (
      <AdminLayout>
        <PageHeader title="Settings" subtitle="Manage departments and course qualification configuration." />
        <Card>
          <div className="flex justify-center py-16"><Spinner className="text-primary" /></div>
        </Card>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <PageHeader title="Settings" subtitle="Manage departments and course qualification configuration." />

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Departments</h2>
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <Input label="Code" value={departmentForm.code} onChange={(event) => setDepartmentForm({ ...departmentForm, code: event.target.value.toUpperCase() })} />
            <Input label="Name" value={departmentForm.name} onChange={(event) => setDepartmentForm({ ...departmentForm, name: event.target.value })} />
            <Input label="Search" value={departmentSearch} onChange={(event) => setDepartmentSearch(event.target.value)} />
          </div>
          <Input
            label="Description (optional)"
            value={departmentForm.description}
            onChange={(event) => setDepartmentForm({ ...departmentForm, description: event.target.value })}
          />
          <div className="mt-3 flex justify-end">
            <Button
              onClick={() => createDepartment.mutate()}
              loading={createDepartment.isPending}
              disabled={!departmentForm.code || !departmentForm.name}
            >
              Add Department
            </Button>
          </div>

          <div className="mt-6 space-y-2">
            {filteredDepartments.length === 0 && <p className="text-sm text-gray-500">No departments match this search.</p>}
            {filteredDepartments.map((item) => (
              <div key={item.id} className="rounded-lg border border-gray-200 p-3 flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-sm text-gray-900">{item.code} · {item.name}</p>
                  {item.description && <p className="text-xs text-gray-500">{item.description}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => toggleDepartment.mutate({ id: item.id, is_active: item.is_active })}
                  className="inline-flex items-center gap-1 rounded border border-gray-200 px-2.5 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                >
                  {item.is_active ? <X className="h-3.5 w-3.5" /> : <Check className="h-3.5 w-3.5" />}
                  {item.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Course Types</h2>
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <Input label="Code" value={typeForm.code} onChange={(event) => setTypeForm({ ...typeForm, code: event.target.value.toUpperCase() })} />
            <Input label="Name" value={typeForm.name} onChange={(event) => setTypeForm({ ...typeForm, name: event.target.value })} />
            <Input label="Search" value={typeSearch} onChange={(event) => setTypeSearch(event.target.value)} />
          </div>
          <Input
            label="Description (optional)"
            value={typeForm.description}
            onChange={(event) => setTypeForm({ ...typeForm, description: event.target.value })}
          />
          <div className="mt-3 flex justify-end">
            <Button
              onClick={() => createCourseType.mutate()}
              loading={createCourseType.isPending}
              disabled={!typeForm.code || !typeForm.name}
            >
              Add Course Type
            </Button>
          </div>

          <div className="mt-6 space-y-2">
            {filteredCourseTypes.length === 0 && <p className="text-sm text-gray-500">No course types match this search.</p>}
            {filteredCourseTypes.map((item) => (
              <div key={item.id} className="rounded-lg border border-gray-200 p-3 flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-sm text-gray-900">{item.code} · {item.name}</p>
                  {item.description && <p className="text-xs text-gray-500">{item.description}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => toggleCourseType.mutate({ id: item.id, is_active: item.is_active })}
                  className="inline-flex items-center gap-1 rounded border border-gray-200 px-2.5 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                >
                  {item.is_active ? <X className="h-3.5 w-3.5" /> : <Check className="h-3.5 w-3.5" />}
                  {item.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Certification Types</h2>
        <div className="mb-4 grid gap-3 sm:grid-cols-4">
          <select
            value={certForm.courseTypeId}
            onChange={(event) => setCertForm({ ...certForm, courseTypeId: event.target.value })}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Select course type</option>
            {activeCourseTypes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.code} — {item.name}
              </option>
            ))}
          </select>
          <Input label="Code" value={certForm.code} onChange={(event) => setCertForm({ ...certForm, code: event.target.value.toUpperCase() })} />
          <Input label="Name" value={certForm.name} onChange={(event) => setCertForm({ ...certForm, name: event.target.value })} />
          <Input label="Search" value={certSearch} onChange={(event) => setCertSearch(event.target.value)} />
        </div>
        <Input
          label="Description (optional)"
          value={certForm.description}
          onChange={(event) => setCertForm({ ...certForm, description: event.target.value })}
        />
        <div className="mt-3 flex justify-end">
          <Button
            onClick={() => createCertificationType.mutate()}
            loading={createCertificationType.isPending}
            disabled={!certForm.courseTypeId || !certForm.code || !certForm.name}
          >
            Add Certification Type
          </Button>
        </div>

        <div className="mt-6 space-y-2">
          {filteredCertifications.length === 0 && <p className="text-sm text-gray-500">No certification options match this search.</p>}
          {filteredCertifications.map((item) => (
            <div key={item.id} className="rounded-lg border border-gray-200 p-3 flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-sm text-gray-900">{item.code} · {item.name}</p>
                <p className="text-xs text-gray-500">
                  {courseTypeNameById.get(item.course_type) ?? 'Unknown course type'}
                </p>
                {item.description && <p className="text-xs text-gray-500">{item.description}</p>}
              </div>
              <button
                type="button"
                onClick={() => toggleCertificationType.mutate({ id: item.id, is_active: item.is_active })}
                className="inline-flex items-center gap-1 rounded border border-gray-200 px-2.5 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
              >
                {item.is_active ? <X className="h-3.5 w-3.5" /> : <Check className="h-3.5 w-3.5" />}
                {item.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </div>
          ))}
        </div>
      </Card>
      <QualificationSettings courseTypes={courseTypes} courseTypesError={courseTypesQuery.error} />
    </AdminLayout>
  )
}
