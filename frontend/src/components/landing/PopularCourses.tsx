'use client'

import { useRef } from 'react'
import Link from 'next/link'
import { ArrowRight, ChevronLeft, ChevronRight, Clock, BarChart2 } from 'lucide-react'
import { useCourses } from '@/hooks/useCourses'
import Spinner from '@/components/ui/Spinner'
import { getCourseCardImage } from '@/lib/courseImages'
import type { Course } from '@/types'

const LEVEL_LABEL: Record<string, string> = {
  BEGINNER: 'Beginner',
  INTERMEDIATE: 'Intermediate',
  ADVANCED: 'Advanced',
  ALL_LEVELS: 'All Levels',
}

function CourseCard({ course }: { course: Course }) {
  return (
    <div className="group flex flex-col w-[260px] sm:w-[280px] flex-shrink-0 snap-start rounded-xl border border-gray-100 bg-white overflow-hidden hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
      {/* thumbnail */}
      <div className="relative h-40 bg-primary/10 overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={course.thumbnail_url || getCourseCardImage(course.category?.name)}
          alt={course.fullname}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        {course.category && (
          <span className="absolute top-2 left-2 rounded-full bg-accent/90 px-2.5 py-0.5 text-[10px] font-bold text-primary-dark uppercase tracking-wide">
            {course.category.name}
          </span>
        )}
      </div>

      {/* body */}
      <div className="flex flex-col flex-1 p-4 gap-2">
        <h3 className="text-sm font-bold text-gray-900 leading-snug line-clamp-2">
          {course.fullname}
        </h3>
        <p className="text-xs text-gray-500 line-clamp-2 flex-1">{course.summary}</p>

        {/* meta row */}
        <div className="flex items-center gap-3 mt-1">
          {course.duration_days && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              {course.duration_days} days
            </span>
          )}
          {course.level && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <BarChart2 className="h-3 w-3" />
              {LEVEL_LABEL[course.level] ?? course.level}
            </span>
          )}
          {course.price && (
            <span className="ml-auto text-xs font-semibold text-primary">
              USD {course.price}
            </span>
          )}
        </div>

        <Link
          href={`/courses/${course.id}`}
          className="mt-2 block rounded-lg border border-primary text-primary text-center text-xs font-semibold py-2 hover:bg-primary hover:text-white transition-colors"
        >
          View Course
        </Link>
      </div>
    </div>
  )
}

export default function PopularCourses() {
  const { data, isLoading } = useCourses()
  const courses = (data?.results ?? []).filter((c) => c.is_active).slice(0, 8)
  const trackRef = useRef<HTMLDivElement>(null)

  const scroll = (dir: 1 | -1) => {
    const track = trackRef.current
    if (!track) return
    track.scrollBy({ left: dir * (track.clientWidth * 0.9), behavior: 'smooth' })
  }

  return (
    <section id="courses" className="py-14 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Popular Courses</h2>
          <div className="flex items-center gap-4">
            <Link
              href="/courses"
              className="text-sm font-medium text-primary hover:text-primary-light inline-flex items-center gap-1"
            >
              View All <ArrowRight className="h-4 w-4" />
            </Link>
            {courses.length > 0 && (
              <div className="hidden sm:flex items-center gap-2">
                <button
                  onClick={() => scroll(-1)}
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600 hover:bg-primary hover:text-white hover:border-primary transition-colors"
                  aria-label="Scroll left"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => scroll(1)}
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600 hover:bg-primary hover:text-white hover:border-primary transition-colors"
                  aria-label="Scroll right"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {isLoading && (
          <div className="flex justify-center py-12">
            <Spinner size="lg" className="text-primary" />
          </div>
        )}

        <div
          ref={trackRef}
          className="flex gap-6 overflow-x-auto scrollbar-hide snap-x snap-mandatory scroll-smooth pb-2"
        >
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>

        {!isLoading && courses.length === 0 && (
          <p className="text-center text-gray-500 py-10">No courses available yet.</p>
        )}
      </div>
    </section>
  )
}
