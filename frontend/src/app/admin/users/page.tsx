'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import Input from '@/components/ui/Input'
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
}

export default function AdminUsersPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading } = useAdminUsers(search)
  const users = data?.results ?? []

  return (
    <AdminLayout>
      <PageHeader title="Users" subtitle={`${data?.count ?? 0} registered users`} />

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
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="py-3">
                      <p className="font-medium text-gray-900">{user.full_name}</p>
                      <p className="text-xs text-gray-500">{user.employee_id || '—'}</p>
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </AdminLayout>
  )
}
