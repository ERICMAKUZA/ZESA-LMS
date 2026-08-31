'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import AdminLayout from '@/components/layout/AdminLayout'
import CourseEditor from '@/components/admin/CourseEditor'
import PageHeader from '@/components/ui/PageHeader'
import Spinner from '@/components/ui/Spinner'
import api from '@/lib/api'
import type { Course } from '@/types'

export default function EditCoursePage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const courseQuery = useQuery<Course>({
    queryKey: ['admin-course', params.id],
    queryFn: async () => (await api.get(`/courses/admin/${params.id}/`)).data,
  })

  useEffect(() => {
    if (courseQuery.isError) router.replace('/admin/courses')
  }, [courseQuery.isError, router])

  if (courseQuery.isError) {
    return null
  }

  return (
    <AdminLayout>
      <PageHeader title="Edit Course" subtitle="Update course details and lecturer assignments." />
      {courseQuery.isLoading || !courseQuery.data ? (
        <div className="flex justify-center py-12"><Spinner className="text-primary" /></div>
      ) : <CourseEditor course={courseQuery.data} />}
    </AdminLayout>
  )
}
