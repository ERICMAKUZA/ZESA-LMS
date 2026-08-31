'use client'

import AdminLayout from '@/components/layout/AdminLayout'
import CourseEditor from '@/components/admin/CourseEditor'
import PageHeader from '@/components/ui/PageHeader'

export default function NewCoursePage() {
  return (
    <AdminLayout>
      <PageHeader title="Add Course" subtitle="Create the course, assign its lecturers, set the first intake, and publish it to Moodle." />
      <CourseEditor />
    </AdminLayout>
  )
}
