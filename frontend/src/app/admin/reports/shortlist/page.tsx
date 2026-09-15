'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import AdminLayout from '@/components/layout/AdminLayout'
import Card from '@/components/ui/Card'
import Select from '@/components/ui/Select'
import Spinner from '@/components/ui/Spinner'
import Button from '@/components/ui/Button'
import { useCourses } from '@/hooks/useCourses'
import api from '@/lib/api'
import type { ShortlistRow } from '@/types'

export default function ShortlistPage() {
  const [courseId, setCourseId] = useState('')
  const { data: coursesData } = useCourses()
  const { data, isLoading } = useQuery<{ course: number; results: ShortlistRow[] }>({
    queryKey: ['qualification-shortlist', courseId],
    queryFn: async () => (await api.get('/reports/shortlist/', { params: { course: courseId } })).data,
    enabled: Boolean(courseId),
  })
  const download = async () => {
    const response = await api.get('/reports/shortlist/', {
      params: { course: courseId, format: 'csv' },
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = 'course-shortlist.csv'
    link.click()
    URL.revokeObjectURL(url)
  }
  return <AdminLayout><div className="mb-6 flex items-start justify-between"><div><h1 className="text-2xl font-bold text-gray-900">Course Shortlist</h1><p className="mt-1 text-sm text-gray-500">Ranked by A-Level science preference, points, then name.</p></div><Link href="/admin/reports" className="text-sm text-primary hover:underline">Back to reports</Link></div><Card className="mb-6"><Select label="Course" value={courseId} onValueChange={setCourseId} options={[{ value: '', label: 'Select a course' }, ...(coursesData?.results ?? []).map((course) => ({ value: String(course.id), label: course.fullname }))]} /></Card>{isLoading && <div className="flex justify-center py-10"><Spinner className="text-primary" /></div>}{data && <Card header={<div className="flex items-center justify-between"><h2 className="font-semibold text-gray-900">Ranked applicants</h2><Button size="sm" onClick={download}>Download CSV</Button></div>}><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead><tr className="border-b text-xs uppercase tracking-wide text-gray-500"><th className="pb-3 text-left">Applicant</th><th className="pb-3 text-left">Points</th><th className="pb-3 text-left">Eligibility</th><th className="pb-3 text-left">Review context</th></tr></thead><tbody className="divide-y divide-gray-100">{data.results.map((row) => <tr key={row.application_id}><td className="py-3 font-medium">{row.surname}, {row.name}</td><td className="py-3">{row.points}</td><td className={`py-3 ${row.eligibility === 'Meets requirements' ? 'text-green-700' : 'text-red-700'}`}>{row.eligibility}</td><td className="py-3 text-xs text-gray-600">{row.has_a_level_sciences ? 'A-Level science' : ''}{row.has_override ? ' · Override recorded' : ''}{row.failed_rule_codes.length ? ` · ${row.failed_rule_codes.join(', ')}` : ''}</td></tr>)}</tbody></table></div>{data.results.length === 0 && <p className="py-8 text-center text-sm text-gray-500">No applicants for this course.</p>}</Card>}</AdminLayout>
}
