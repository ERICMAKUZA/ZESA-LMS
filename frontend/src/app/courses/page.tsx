'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, BookOpen, ArrowRight } from 'lucide-react'
import StudentLayout from '@/components/layout/StudentLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Spinner from '@/components/ui/Spinner'
import Button from '@/components/ui/Button'
import { useCourses } from '@/hooks/useCourses'

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

export default function CoursesPage() {
  const { data, isLoading } = useCourses()
  const [search, setSearch] = useState('')

  const courses = (data?.results ?? []).filter(
    (c) => c.is_active && c.fullname.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <StudentLayout>
      <PageHeader title="Course Catalogue" subtitle="Browse available training programmes." />

      <div className="mb-6 max-w-sm">
        <Input
          placeholder="Search courses…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner size="lg" className="text-primary" />
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {courses.map((course) => (
          <Card key={course.id} className="flex flex-col">
            <div className="h-28 bg-primary/10 rounded-t-lg flex items-center justify-center">
              <BookOpen className="h-8 w-8 text-primary/40" />
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
                <CapacityBadge max={course.max_capacity} enrolled={course.enrolled_count} />
                {course.duration_days && (
                  <span className="text-xs text-gray-400">{course.duration_days}d</span>
                )}
              </div>
              <div className="mt-auto pt-3 flex gap-2">
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

      {!isLoading && courses.length === 0 && (
        <p className="py-10 text-center text-sm text-gray-500">
          {search ? `No courses match "${search}".` : 'No courses available.'}
        </p>
      )}
    </StudentLayout>
  )
}
