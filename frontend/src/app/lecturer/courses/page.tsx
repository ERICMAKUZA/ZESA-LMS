'use client'

import { CalendarDays } from 'lucide-react'
import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { useLecturerSchedules } from '@/hooks/useLecturer'

const statusStyle: Record<string, string> = {
  OPEN: 'bg-green-100 text-green-700',
  FULL: 'bg-amber-100 text-amber-700',
  CANCELLED: 'bg-red-100 text-red-700',
  COMPLETED: 'bg-gray-100 text-gray-600',
}

export default function LecturerCoursesPage() {
  const { data: schedules = [], isLoading } = useLecturerSchedules()

  return (
    <AdminLayout>
      <PageHeader title="My Courses" subtitle={`${schedules.length} assigned intake${schedules.length === 1 ? '' : 's'}`} />

      <Card>
        {isLoading && (
          <div className="flex justify-center py-10">
            <Spinner className="text-primary" />
          </div>
        )}

        {!isLoading && schedules.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500">
            You haven&apos;t been assigned to any course intakes yet.
          </p>
        )}

        {!isLoading && schedules.length > 0 && (
          <div className="divide-y divide-gray-100">
            {schedules.map((s) => (
              <div key={s.id} className="flex items-center justify-between py-4">
                <div className="flex items-center gap-3">
                  <CalendarDays className="h-5 w-5 shrink-0 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900">{s.course_name}</p>
                    <p className="text-xs text-gray-500">
                      {s.month_display} Week {s.week_in_month} {s.year} · {s.category}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500 hidden sm:inline">
                    {s.enrolled_count} / {s.max_capacity} enrolled
                  </span>
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusStyle[s.status] ?? 'bg-gray-100 text-gray-700'}`}>
                    {s.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </AdminLayout>
  )
}
