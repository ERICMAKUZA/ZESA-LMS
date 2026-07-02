'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { BookOpen, DollarSign, ArrowLeft } from 'lucide-react'
import StudentLayout from '@/components/layout/StudentLayout'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useCourse } from '@/hooks/useCourses'
import { useAuth } from '@/hooks/useAuth'

function CapacityBadge({ max, enrolled }: { max: number | null; enrolled: number }) {
  if (!max) return null
  const remaining = max - enrolled
  const pct = enrolled / max
  if (remaining <= 0)
    return (
      <span className="inline-block text-xs font-semibold bg-red-100 text-red-700 rounded-full px-2 py-0.5">
        Full
      </span>
    )
  if (pct >= 0.85)
    return (
      <span className="inline-block text-xs font-semibold bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">
        {remaining} place{remaining !== 1 ? 's' : ''} left
      </span>
    )
  return (
    <span className="inline-block text-xs font-semibold bg-green-100 text-green-700 rounded-full px-2 py-0.5">
      Open
    </span>
  )
}

export default function CourseDetailPage({ params }: { params: { id: string } }) {
  const { data: course, isLoading, isError } = useCourse(params.id)
  const { user } = useAuth()
  const router = useRouter()

  const isFull = course
    ? course.max_capacity !== null && course.enrolled_count >= course.max_capacity
    : false

  const handleApply = () => {
    const dest = `/applications/new?course=${course!.id}`
    if (!user) {
      router.push(`/login?next=${encodeURIComponent(dest)}`)
    } else {
      router.push(dest)
    }
  }

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
                {course.duration_days && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Duration</span>
                    <span className="text-gray-800">{course.duration_days} days</span>
                  </div>
                )}
                {course.level && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Level</span>
                    <span className="text-gray-800">{course.level}</span>
                  </div>
                )}

                {/* Capacity row */}
                {course.max_capacity && (
                  <div className="flex items-center justify-between py-3 border-t border-gray-100">
                    <span className="text-sm text-gray-500">Availability</span>
                    <div className="flex items-center gap-2">
                      <CapacityBadge max={course.max_capacity} enrolled={course.enrolled_count} />
                      <span className="text-xs text-gray-400">
                        ({course.enrolled_count} / {course.max_capacity} enrolled)
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {course.requires_approval && course.is_active && (
                <Button
                  className="mt-4 w-full"
                  disabled={isFull}
                  onClick={handleApply}
                >
                  {isFull ? 'Course Full' : 'Apply for This Course'}
                </Button>
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
