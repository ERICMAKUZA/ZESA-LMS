'use client'

import Link from 'next/link'
import { BookOpen, Award, Users, ArrowRight } from 'lucide-react'
import PublicLayout from '@/components/layout/PublicLayout'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { useCourses } from '@/hooks/useCourses'

export default function LandingPage() {
  const { data, isLoading } = useCourses()
  const featured = data?.results.filter((c) => c.is_active).slice(0, 6) ?? []

  return (
    <PublicLayout>
      {/* Hero */}
      <section className="bg-primary text-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            ZESA Integrated Learning<br />Management Platform
          </h1>
          <p className="mt-4 text-lg text-white/80 max-w-2xl mx-auto">
            Access professional development courses, submit training applications, and earn recognised
            certifications — all in one place.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link
              href="/register"
              className="rounded-md bg-accent px-6 py-3 text-base font-semibold text-white hover:bg-accent-light"
            >
              Apply Now
            </Link>
            <Link
              href="/courses"
              className="flex items-center gap-1.5 rounded-md border border-white/40 px-6 py-3 text-base font-semibold text-white hover:bg-white/10"
            >
              Browse Courses <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-14 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="grid gap-8 sm:grid-cols-3">
            {[
              { icon: BookOpen, title: 'Structured Courses', desc: 'Curated technical and soft-skills training programmes designed for ZESA employees.' },
              { icon: Users,    title: 'Manager Approval',   desc: 'Seamless multi-step approval workflow with your line manager and HR.' },
              { icon: Award,    title: 'Certified Outcomes', desc: 'Earn verifiable digital certificates on course completion.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex flex-col items-center text-center p-6 rounded-lg border border-gray-100">
                <Icon className="h-10 w-10 text-primary mb-3" />
                <h3 className="font-semibold text-gray-900">{title}</h3>
                <p className="mt-2 text-sm text-gray-600">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured courses */}
      <section className="py-14 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">Featured Courses</h2>
          {isLoading && (
            <div className="flex justify-center py-10">
              <Spinner size="lg" className="text-primary" />
            </div>
          )}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((course) => (
              <Card key={course.id} className="flex flex-col">
                <div className="h-32 rounded-t-lg bg-primary/10 flex items-center justify-center">
                  <BookOpen className="h-10 w-10 text-primary/50" />
                </div>
                <div className="p-4 flex flex-col gap-2 flex-1">
                  <span className="text-xs font-medium text-accent">{course.category?.name}</span>
                  <h3 className="font-semibold text-gray-900 leading-snug">{course.fullname}</h3>
                  <p className="text-sm text-gray-600 line-clamp-2">{course.summary}</p>
                  <div className="mt-auto pt-3">
                    <Link
                      href={`/courses/${course.id}`}
                      className="text-sm font-medium text-primary hover:underline inline-flex items-center gap-1"
                    >
                      View details <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              </Card>
            ))}
          </div>
          {!isLoading && featured.length === 0 && (
            <p className="text-center text-gray-500 py-10">No courses available yet.</p>
          )}
        </div>
      </section>
    </PublicLayout>
  )
}
