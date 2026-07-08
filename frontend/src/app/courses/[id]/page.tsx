'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { DollarSign, ArrowLeft } from 'lucide-react'
import Image from 'next/image'
import { getCourseHeroImage } from '@/lib/courseImages'
import PublicLayout from '@/components/layout/PublicLayout'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import { useCourse } from '@/hooks/useCourses'
import { useAuth } from '@/hooks/useAuth'
import EnquiryModal from '@/components/EnquiryModal'
import type { CourseSchedule } from '@/types'

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

function ScheduleStatusBadge({ s }: { s: CourseSchedule }) {
  if (s.status === 'FULL')
    return <span className="text-xs font-semibold bg-red-100 text-red-700 rounded-full px-2.5 py-1">Full</span>
  if (s.places_remaining <= 3)
    return (
      <span className="text-xs font-semibold bg-amber-100 text-amber-700 rounded-full px-2.5 py-1">
        {s.places_remaining} left
      </span>
    )
  return <span className="text-xs font-semibold bg-green-100 text-green-700 rounded-full px-2.5 py-1">Open</span>
}

export default function CourseDetailPage({ params }: { params: { id: string } }) {
  const { data: course, isLoading, isError } = useCourse(params.id)
  const { user } = useAuth()
  const router = useRouter()
  const [enquiryOpen, setEnquiryOpen] = useState(false)

  const isFull = course
    ? course.max_capacity !== null && course.enrolled_count >= course.max_capacity
    : false

  const handleApply = (scheduleId?: string) => {
    const params = new URLSearchParams({ course: String(course!.id) })
    if (scheduleId) params.set('schedule', scheduleId)
    const dest = `/applications/new?${params}`
    if (!user) {
      router.push(`/login?next=${encodeURIComponent(dest)}`)
    } else {
      router.push(dest)
    }
  }

  return (
    <PublicLayout>
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
          {/* Main column */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Description card */}
            <Card className="overflow-hidden">
              <div className="relative h-52 -mx-6 -mt-4 mb-4 rounded-t-lg overflow-hidden">
                <Image
                  src={getCourseHeroImage(course.category?.name)}
                  alt={course.category?.name ?? course.fullname}
                  fill
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 66vw"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                {course.category && (
                  <span className="absolute bottom-3 left-4 text-xs font-semibold text-white/90 uppercase tracking-wide">
                    {course.category.name}
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-bold text-gray-900">{course.fullname}</h1>
              <p className="mt-3 text-sm text-gray-700 leading-relaxed whitespace-pre-line">{course.summary}</p>
            </Card>

            {/* Upcoming intakes */}
            {course.upcoming_schedules && course.upcoming_schedules.length > 0 && (
              <Card>
                <h3 className="text-base font-semibold text-gray-800 mb-3">Upcoming Intakes</h3>
                <div className="space-y-2">
                  {course.upcoming_schedules.map(s => (
                    <div
                      key={s.id}
                      className="flex items-center justify-between px-4 py-3 rounded-lg bg-gray-50 border border-gray-200"
                    >
                      <div>
                        <span className="text-sm font-medium text-gray-800">
                          {s.month_display} {s.year} — Week {s.week_in_month}
                        </span>
                        <span className="text-xs text-gray-400 ml-2">
                          (~{s.approximate_start_date} to {s.approximate_end_date})
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <ScheduleStatusBadge s={s} />
                        <button
                          onClick={() => handleApply(s.id)}
                          disabled={s.status === 'FULL'}
                          className="text-xs font-medium text-green-700 hover:text-green-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                        >
                          {s.status === 'FULL' ? 'Full' : 'Apply →'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Sidebar */}
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
                  onClick={() => handleApply()}
                >
                  {isFull ? 'Course Full' : 'Apply for This Course'}
                </Button>
              )}
              {!course.is_active && (
                <p className="mt-4 text-xs text-gray-400 text-center">This course is currently inactive.</p>
              )}

              <button
                onClick={() => setEnquiryOpen(true)}
                className="mt-3 w-full text-center text-xs text-green-700 hover:text-green-900 underline underline-offset-2"
              >
                Have questions? Enquire about this course
              </button>
            </Card>
          </div>
        </div>
      )}

      {course && (
        <EnquiryModal
          open={enquiryOpen}
          onClose={() => setEnquiryOpen(false)}
          preselectedCourse={{ id: String(course.id), fullname: course.fullname }}
        />
      )}
    </PublicLayout>
  )
}
