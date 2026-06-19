'use client'

import Link from 'next/link'
import { BookOpen, DollarSign, ArrowLeft } from 'lucide-react'
import StudentLayout from '@/components/layout/StudentLayout'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useCourse } from '@/hooks/useCourses'

export default function CourseDetailPage({ params }: { params: { id: string } }) {
  const { data: course, isLoading, isError } = useCourse(params.id)

  return (
    <StudentLayout>
      <div className="mb-4">
        <Link href="/courses" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary">
          <ArrowLeft className="h-4 w-4" /> Back to courses
        </Link>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner size="lg" className="text-primary" />
        </div>
      )}

      {isError && (
        <p className="text-center text-sm text-gray-500 py-10">Course not found.</p>
      )}

      {course && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 flex flex-col gap-6">
            <Card>
              <div className="h-40 bg-primary/10 rounded-t-lg flex items-center justify-center -mx-6 -mt-4 mb-4">
                <BookOpen className="h-12 w-12 text-primary/40" />
              </div>
              {course.category && (
                <span className="text-xs font-medium text-accent">{course.category.name}</span>
              )}
              <h1 className="mt-1 text-2xl font-bold text-gray-900">{course.fullname}</h1>
              <p className="mt-3 text-sm text-gray-700 leading-relaxed whitespace-pre-line">{course.summary}</p>
            </Card>

          </div>

          <div className="flex flex-col gap-4">
            <Card>
              <h2 className="font-semibold text-gray-900 mb-4">Course Info</h2>
              <div className="flex flex-col gap-3">
                {course.price && (
                  <div className="flex items-center gap-2 text-sm">
                    <DollarSign className="h-4 w-4 text-gray-400" />
                    <span>USD {course.price}</span>
                  </div>
                )}
              </div>
              {course.requires_approval && course.is_active && (
                <Link href={`/applications/new?courseId=${course.id}`} className="mt-6 block">
                  <Button className="w-full">Apply for this course</Button>
                </Link>
              )}
              {!course.is_active && (
                <p className="mt-4 text-xs text-gray-400 text-center">This course is currently inactive.</p>
              )}
            </Card>
          </div>
        </div>
      )}
    </StudentLayout>
  )
}
