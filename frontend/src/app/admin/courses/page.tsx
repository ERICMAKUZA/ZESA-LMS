'use client'

import { useState } from 'react'
import Link from 'next/link'
import { BookOpen } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import Input from '@/components/ui/Input'
import api from '@/lib/api'
import type { Course, PaginatedResponse } from '@/types'

function useAdminCourses(search: string) {
  return useQuery<PaginatedResponse<Course>>({
    queryKey: ['admin-courses', search],
    queryFn: async () => {
      const { data } = await api.get('/courses/admin/', { params: search ? { search } : undefined })
      return data
    },
  })
}

export default function AdminCoursesPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading } = useAdminCourses(search)
  const courses = data?.results ?? []

  return (
    <AdminLayout>
      <PageHeader title="Courses" subtitle={`${data?.count ?? 0} total courses`} />

      <div className="mb-6 max-w-sm">
        <Input
          placeholder="Search courses…"
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

        {!isLoading && courses.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">No courses found.</p>
        )}

        {!isLoading && courses.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                  <th className="pb-3 text-left font-medium">Course</th>
                  <th className="pb-3 text-left font-medium hidden sm:table-cell">Category</th>
                  <th className="pb-3 text-left font-medium hidden md:table-cell">Price</th>
                  <th className="pb-3 text-left font-medium">Status</th>
                  <th className="pb-3 text-left font-medium hidden lg:table-cell">Enrolled</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {courses.map((course) => (
                  <tr key={course.id}>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-gray-400 shrink-0" />
                        <div>
                          <p className="font-medium text-gray-900">{course.fullname}</p>
                          <p className="text-xs text-gray-500">{course.shortname}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 text-gray-600 hidden sm:table-cell">
                      {course.category?.name ?? '—'}
                    </td>
                    <td className="py-3 text-gray-600 hidden md:table-cell">
                      {course.price ? `USD ${course.price}` : 'Free'}
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          course.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {course.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600 hidden lg:table-cell">
                      {course.enrolled_count}
                      {course.max_capacity ? ` / ${course.max_capacity}` : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <p className="mt-4 text-xs text-gray-400 text-center">
        To add or edit courses, use the{' '}
        <Link href="/django-admin/courses/course/" className="text-primary hover:underline" target="_blank">
          Django admin
        </Link>.
      </p>
    </AdminLayout>
  )
}
