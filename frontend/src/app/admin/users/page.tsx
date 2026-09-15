'use client'

import { type FormEvent, useMemo, useState } from 'react'
import { UserPlus, Plus, Play, Ban } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import api from '@/lib/api'
import type { User, PaginatedResponse } from '@/types'

function useAdminUsers(search: string) {
  return useQuery<PaginatedResponse<User>>({
    queryKey: ['admin-users', search],
    queryFn: async () => {
      const { data } = await api.get('/admin/users/', { params: search ? { search } : undefined })
      return data
    },
  })
}

const roleBadge: Record<string, string> = {
  STUDENT:    'bg-blue-100 text-blue-700',
  REVIEWER:   'bg-yellow-100 text-yellow-800',
  FINANCE:    'bg-teal-100 text-teal-700',
  ADMIN:      'bg-primary/10 text-primary',
  SUPERADMIN: 'bg-purple-100 text-purple-700',
  TRAINER:    'bg-indigo-100 text-indigo-700',
  CENTRE_ADMIN:'bg-orange-100 text-orange-700',
  LECTURER:   'bg-fuchsia-100 text-fuchsia-700',
}

function parseErrorMessage(err: unknown): string | undefined {
  const response = (err as { response?: { data?: { detail?: string | undefined; [key: string]: unknown } } })?.response
  if (!response?.data) return undefined
  if (typeof response.data.detail === 'string') {
    return response.data.detail
  }
  const firstStringError = Object.values(response.data).find((value): value is string => typeof value === 'string')
  return firstStringError ?? undefined
}

type CreateUserForm = {
  first_name: string
  last_name: string
  email: string
  employee_id: string
  department: string
  phone: string
  role: 'TRAINER' | 'LECTURER'
  password: string
  password_confirm: string
}

const defaultCreateForm: CreateUserForm = {
  first_name: '',
  last_name: '',
  email: '',
  employee_id: '',
  department: '',
  phone: '',
  role: 'TRAINER',
  password: '',
  password_confirm: '',
}

export default function AdminUsersPage() {
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState<CreateUserForm>(defaultCreateForm)
  const [actionUserId, setActionUserId] = useState<number | null>(null)
  const [actionType, setActionType] = useState<'assign' | 'deactivate' | 'reactivate' | null>(null)

  const { data, isLoading } = useAdminUsers(search)
  const users = data?.results ?? []
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const invalidateUsers = () => queryClient.invalidateQueries({ queryKey: ['admin-users'] })

  const createMutation = useMutation({
    mutationFn: async (payload: CreateUserForm) => {
      const { data } = await api.post('/admin/users/', payload)
      return data
    },
    onSuccess: () => {
      toast({ variant: 'success', title: 'User created', description: 'Account has been created and is ready to use.' })
      invalidateUsers()
      setCreateOpen(false)
      setForm(defaultCreateForm)
    },
    onError: (error) => {
      toast({ variant: 'error', title: 'Create failed', description: parseErrorMessage(error) ?? 'Check the form values and try again.' })
    },
  })

  const assignLecturerMutation = useMutation({
    mutationFn: async (userId: number) => {
      const { data } = await api.post(`/admin/users/${userId}/assign-lecturer/`)
      return data
    },
    onSuccess: () => {
      toast({ variant: 'success', title: 'Lecturer assigned' })
      invalidateUsers()
      setActionUserId(null)
      setActionType(null)
    },
    onError: (error) => {
      toast({ variant: 'error', title: 'Action failed', description: parseErrorMessage(error) ?? 'Could not assign lecturer role.' })
      setActionUserId(null)
      setActionType(null)
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: async (userId: number) => {
      const { data } = await api.post(`/admin/users/${userId}/deactivate/`)
      return data
    },
    onSuccess: () => {
      toast({ variant: 'success', title: 'User deactivated' })
      invalidateUsers()
      setActionUserId(null)
      setActionType(null)
    },
    onError: (error) => {
      toast({ variant: 'error', title: 'Action failed', description: parseErrorMessage(error) ?? 'Could not deactivate user.' })
      setActionUserId(null)
      setActionType(null)
    },
  })

  const reactivateMutation = useMutation({
    mutationFn: async (userId: number) => {
      const { data } = await api.post(`/admin/users/${userId}/reactivate/`)
      return data
    },
    onSuccess: () => {
      toast({ variant: 'success', title: 'User reactivated' })
      invalidateUsers()
      setActionUserId(null)
      setActionType(null)
    },
    onError: (error) => {
      toast({ variant: 'error', title: 'Action failed', description: parseErrorMessage(error) ?? 'Could not reactivate user.' })
      setActionUserId(null)
      setActionType(null)
    },
  })

  const setField = (field: keyof CreateUserForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const submitCreate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!form.first_name.trim() || !form.last_name.trim() || !form.email.trim() || !form.role || !form.password || !form.password_confirm) {
      toast({ variant: 'error', title: 'Missing details', description: 'First name, last name, email, role and password are required.' })
      return
    }
    if (form.password !== form.password_confirm) {
      toast({ variant: 'error', title: 'Passwords must match', description: 'Please confirm the same password before creating the account.' })
      return
    }
    createMutation.mutate(form)
  }

  const closeCreate = () => {
    setCreateOpen(false)
    setForm(defaultCreateForm)
  }

  const isBusy = [
    createMutation.isPending,
    assignLecturerMutation.isPending,
    deactivateMutation.isPending,
    reactivateMutation.isPending,
  ].some(Boolean)

  const isUserBusy = (id: number, type: 'assign' | 'deactivate' | 'reactivate') =>
    actionUserId === id && actionType === type && isBusy

  const roleOptions = useMemo(() => [
    { value: 'TRAINER', label: 'Trainer' },
    { value: 'LECTURER', label: 'Lecturer' },
  ], [])

  return (
    <AdminLayout>
      <PageHeader
        title="Users"
        subtitle={`${data?.count ?? 0} registered users`}
        action={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" /> Add User
          </Button>
        }
      />

      <div className="mb-6 max-w-sm">
        <Input
          placeholder="Search by name, email or employee ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && users.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">No users found.</p>
        )}

        {!isLoading && users.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                  <th className="pb-3 text-left font-medium">Name</th>
                  <th className="pb-3 text-left font-medium hidden sm:table-cell">Email</th>
                  <th className="pb-3 text-left font-medium">Role</th>
                  <th className="pb-3 text-left font-medium hidden md:table-cell">Department</th>
                  <th className="pb-3 text-left font-medium hidden lg:table-cell">Joined</th>
                  <th className="pb-3 text-left font-medium">Active</th>
                  <th className="pb-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="py-3">
                      <p className="font-medium text-gray-900">{user.full_name}</p>
                      <p className="text-xs text-gray-500">
                        {user.employee_id || '—'}
                        {user.ec_number && ` · ${user.ec_number}`}
                      </p>
                    </td>
                    <td className="py-3 text-gray-600 hidden sm:table-cell">{user.email}</td>
                    <td className="py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${roleBadge[user.role] ?? 'bg-gray-100 text-gray-700'}`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600 hidden md:table-cell">{user.department || '—'}</td>
                    <td className="py-3 text-gray-500 hidden lg:table-cell">
                      {format(new Date(user.date_joined), 'dd MMM yyyy')}
                    </td>
                    <td className="py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex justify-end gap-2">
                        {!(user.role === 'LECTURER' || user.role === 'TRAINER' || user.role === 'ADMIN' || user.role === 'SUPERADMIN') && (
                          <Button
                            size="sm"
                            variant="outline"
                            loading={isUserBusy(user.id, 'assign')}
                            onClick={() => {
                              setActionUserId(user.id)
                              setActionType('assign')
                              assignLecturerMutation.mutate(user.id)
                            }}
                          >
                            <UserPlus className="h-4 w-4" />
                            Assign lecturer
                          </Button>
                        )}
                        {(user.role === 'TRAINER' || user.role === 'LECTURER') && user.is_active && (
                          <Button
                            size="sm"
                            variant="outline"
                            loading={isUserBusy(user.id, 'deactivate')}
                            onClick={() => {
                              setActionUserId(user.id)
                              setActionType('deactivate')
                              deactivateMutation.mutate(user.id)
                            }}
                          >
                            <Ban className="h-4 w-4" /> Deactivate
                          </Button>
                        )}
                        {!user.is_active && (
                          <Button
                            size="sm"
                            variant="outline"
                            loading={isUserBusy(user.id, 'reactivate')}
                            onClick={() => {
                              setActionUserId(user.id)
                              setActionType('reactivate')
                              reactivateMutation.mutate(user.id)
                            }}
                          >
                            <Play className="h-4 w-4" /> Reactivate
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal
        open={createOpen}
        onOpenChange={(open) => {
          if (!open) {
            closeCreate()
          } else {
            setCreateOpen(true)
          }
        }}
        title="Create Staff User"
        footer={
          <>
            <Button variant="ghost" onClick={closeCreate}>Cancel</Button>
            <Button loading={createMutation.isPending} onClick={() => {
              const formElement = document.getElementById('create-user-form') as HTMLFormElement | null
              formElement?.requestSubmit()
            }}>Create</Button>
          </>
        }
      >
        <form id="create-user-form" onSubmit={submitCreate} className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <Input
              label="First name"
              value={form.first_name}
              onChange={(event) => setField('first_name', event.target.value)}
              required
            />
            <Input
              label="Last name"
              value={form.last_name}
              onChange={(event) => setField('last_name', event.target.value)}
              required
            />
          </div>
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => setField('email', event.target.value)}
            required
          />
          <div className="grid gap-3 md:grid-cols-2">
            <Input
              label="Employee ID"
              value={form.employee_id}
              onChange={(event) => setField('employee_id', event.target.value)}
            />
            <Input
              label="Department"
              value={form.department}
              onChange={(event) => setField('department', event.target.value)}
            />
          </div>
          <Input
            label="Phone"
            type="tel"
            value={form.phone}
            onChange={(event) => setField('phone', event.target.value)}
          />
          <Select
            label="Role"
            value={form.role}
            options={roleOptions}
            onValueChange={(value) => setField('role', value)}
          />
          <div className="grid gap-3 md:grid-cols-2">
            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={(event) => setField('password', event.target.value)}
              required
            />
            <Input
              label="Confirm password"
              type="password"
              value={form.password_confirm}
              onChange={(event) => setField('password_confirm', event.target.value)}
              required
            />
          </div>
        </form>
      </Modal>
    </AdminLayout>
  )
}
