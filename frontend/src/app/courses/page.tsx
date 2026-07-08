'use client'

import React, { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import Image from 'next/image'
import { getCourseCardImage } from '@/lib/courseImages'
import publicApi from '@/lib/publicApi'
import PublicLayout from '@/components/layout/PublicLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Spinner from '@/components/ui/Spinner'
import Button from '@/components/ui/Button'
import type { Course, CourseCategory, CourseSchedule } from '@/types'
import { FAQSection } from '@/components/FAQSection'
import EnquiryModal from '@/components/EnquiryModal'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const MONTH_NAMES = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December',
]

interface ScheduleMonthGroup {
  month: number
  month_display: string
  schedules: CourseSchedule[]
}

function CapacityBadge({ max, enrolled }: { max: number | null; enrolled: number }) {
  if (!max) return null
  const remaining = max - enrolled
  const pct = enrolled / max
  if (remaining <= 0)
    return <span className="text-xs font-semibold bg-red-100 text-red-700 rounded-full px-2 py-0.5">Full</span>
  if (pct >= 0.85)
    return <span className="text-xs font-semibold bg-amber-100 text-amber-700 rounded-full px-2 py-0.5">{remaining} left</span>
  return <span className="text-xs font-semibold bg-green-100 text-green-700 rounded-full px-2 py-0.5">Open</span>
}

function NextAvailableBadge({ nextSchedule }: { nextSchedule: CourseSchedule | null }) {
  if (!nextSchedule)
    return <span className="text-xs text-gray-400">No upcoming dates</span>
  const label = `${nextSchedule.month_display}, Week ${nextSchedule.week_in_month}`
  if (nextSchedule.status === 'FULL')
    return <span className="text-xs text-red-600 font-medium">Full — Next: {label}</span>
  if (nextSchedule.places_remaining <= 3)
    return (
      <span className="text-xs text-amber-600 font-medium">
        {nextSchedule.places_remaining} place{nextSchedule.places_remaining !== 1 ? 's' : ''} left — {label}
      </span>
    )
  return <span className="text-xs text-green-700 font-medium">Next: {label}</span>
}

function CoursesContent() {
  const searchParams = useSearchParams()

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [enquiryOpen, setEnquiryOpen] = useState(false)

  useEffect(() => {
    const cat = searchParams.get('category')
    if (cat) setSelectedCategory(cat)
  }, [searchParams])

  const { data: categories = [] } = useQuery<CourseCategory[]>({
    queryKey: ['categories'],
    queryFn: () => publicApi.get('/courses/categories/').then(r => r.data),
  })

  const { data: courses = [], isLoading } = useQuery<Course[]>({
    queryKey: ['courses', selectedCategory],
    queryFn: () =>
      publicApi.get('/courses/', {
        params: selectedCategory ? { category: selectedCategory } : {},
      }).then(r => r.data.results ?? r.data),
  })

  const { data: monthData } = useQuery<ScheduleMonthGroup[]>({
    queryKey: ['schedule', selectedMonth],
    queryFn: () =>
      publicApi.get('/courses/schedule/', { params: { month: selectedMonth } }).then(r => r.data),
    enabled: !!selectedMonth,
  })

  const filteredCourses = search
    ? courses.filter(c => c.fullname.toLowerCase().includes(search.toLowerCase()))
    : courses

  const selectedCategoryName = categories.find(c => String(c.id) === selectedCategory)?.name
  const monthScheduleGroup = monthData?.[0]

  return (
    <PublicLayout>
      <PageHeader title="Course Catalogue" subtitle="Browse available training programmes." />

      {/* Category filter chips */}
      <div className="flex flex-wrap gap-2 mb-5">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
            !selectedCategory
              ? 'bg-green-700 text-white border-green-700'
              : 'bg-white text-gray-600 border-gray-300 hover:border-green-500'
          }`}
        >
          All Courses
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(selectedCategory === String(cat.id) ? null : String(cat.id))}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors border ${
              selectedCategory === String(cat.id)
                ? 'bg-green-700 text-white border-green-700'
                : 'bg-white text-gray-600 border-gray-300 hover:border-green-500'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Month filter chips */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        <button
          onClick={() => setSelectedMonth(null)}
          className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
            !selectedMonth
              ? 'bg-gray-800 text-white border-gray-800'
              : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
          }`}
        >
          All months
        </button>
        {MONTHS.map((name, i) => (
          <button
            key={i}
            onClick={() => setSelectedMonth(selectedMonth === i + 1 ? null : i + 1)}
            className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
              selectedMonth === i + 1
                ? 'bg-gray-800 text-white border-gray-800'
                : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Course grid mode */}
      {!selectedMonth && (
        <>
          <div className="max-w-sm mb-3">
            <Input
              placeholder="Search courses…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <p className="text-sm text-gray-500 mb-5">
            {filteredCourses.length} course{filteredCourses.length !== 1 ? 's' : ''}
            {selectedCategory ? ` in ${selectedCategoryName}` : ' available'}
          </p>

          {isLoading && (
            <div className="flex justify-center py-12">
              <Spinner size="lg" className="text-primary" />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredCourses.map(course => (
              <Card key={course.id} className="flex flex-col overflow-hidden">
                <div className="relative h-36 -mx-4 -mt-4 mb-0">
                  <Image
                    src={getCourseCardImage(course.category?.name)}
                    alt={course.category?.name ?? 'Course'}
                    fill
                    className="object-cover"
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                </div>
                <div className="p-4 flex flex-col flex-1 gap-2">
                  <span className="text-xs font-medium text-accent">{course.category?.name}</span>
                  <h3 className="font-semibold text-gray-900 leading-snug">{course.fullname}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2">{course.summary}</p>
                  {course.price && (
                    <p className="text-sm font-medium text-primary">USD {course.price}</p>
                  )}
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    {course.level && (
                      <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">
                        {course.level}
                      </span>
                    )}
                    {course.duration_days && (
                      <span className="text-xs text-gray-400">{course.duration_days}d</span>
                    )}
                  </div>

                  {/* Availability + next intake */}
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                    <NextAvailableBadge nextSchedule={course.next_schedule} />
                    <CapacityBadge max={course.max_capacity} enrolled={course.enrolled_count} />
                  </div>

                  <div className="mt-auto pt-2 flex gap-2">
                    <Link href={`/courses/${course.id}`}>
                      <Button variant="outline" size="sm">
                        Details <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
                    {course.requires_approval && (
                      <Link href={`/applications/new?course=${course.id}`}>
                        <Button
                          size="sm"
                          disabled={course.max_capacity !== null && course.enrolled_count >= course.max_capacity}
                        >
                          {course.max_capacity !== null && course.enrolled_count >= course.max_capacity
                            ? 'Course Full'
                            : 'Apply'}
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {!isLoading && filteredCourses.length === 0 && (
            <p className="py-10 text-center text-sm text-gray-500">
              {selectedCategoryName
                ? `No courses found in "${selectedCategoryName}"${search ? ` matching "${search}"` : ''}.`
                : search
                ? `No courses match "${search}".`
                : 'No courses available.'}
            </p>
          )}
        </>
      )}

      {/* Month schedule mode */}
      {selectedMonth && (
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Courses running in {MONTH_NAMES[selectedMonth - 1]} 2026
          </h2>

          {monthData && monthData.length === 0 && (
            <p className="text-gray-500">No courses scheduled this month.</p>
          )}

          {!monthData && (
            <div className="flex justify-center py-12">
              <Spinner size="lg" className="text-primary" />
            </div>
          )}

          <div className="space-y-3">
            {monthScheduleGroup?.schedules?.map(s => (
              <div
                key={s.id}
                className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg hover:border-green-400 transition-colors"
              >
                <div className="w-16 shrink-0 text-center">
                  <span className="text-xs font-bold text-white bg-green-700 rounded px-2 py-1 block">
                    Wk {s.week_in_month}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{s.course_name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {s.category} · {s.approximate_start_date} → {s.approximate_end_date}
                    {s.course_duration_days ? ` · ${s.course_duration_days}d` : ''}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  {s.course_price && (
                    <p className="text-sm font-bold text-gray-800">USD {s.course_price}</p>
                  )}
                  {s.status === 'FULL' ? (
                    <span className="text-xs text-red-600">Full</span>
                  ) : (
                    <span className="text-xs text-green-700">{s.places_remaining} places</span>
                  )}
                </div>
                <Link
                  href={`/courses/${s.course}`}
                  className="text-green-700 text-sm font-medium hover:text-green-900 shrink-0"
                >
                  View →
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      <FAQSection onEnquire={() => setEnquiryOpen(true)} />
      <EnquiryModal open={enquiryOpen} onClose={() => setEnquiryOpen(false)} />
    </PublicLayout>
  )
}

export default function CoursesPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-12">
          <Spinner size="lg" className="text-primary" />
        </div>
      }
    >
      <CoursesContent />
    </Suspense>
  )
}
