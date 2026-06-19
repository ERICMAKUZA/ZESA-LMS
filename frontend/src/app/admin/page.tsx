'use client'

import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { useDashboardStats } from '@/hooks/useApplications'

interface StatCardProps { label: string; value: number | undefined; color?: string }

function StatCard({ label, value, color = 'text-primary' }: StatCardProps) {
  return (
    <Card className="text-center">
      <p className={`text-4xl font-bold ${color}`}>{value ?? '—'}</p>
      <p className="mt-1 text-xs text-gray-500">{label}</p>
    </Card>
  )
}

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useDashboardStats()

  return (
    <AdminLayout>
      <PageHeader title="Admin Dashboard" subtitle="Application pipeline overview." />

      {isLoading && (
        <div className="flex justify-center py-12">
          <Spinner size="lg" className="text-primary" />
        </div>
      )}

      {!isLoading && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-8">
            <StatCard label="Pending Review"           value={stats?.pending_review}           color="text-yellow-600" />
            <StatCard label="Approved (Awaiting Pay)"  value={stats?.approved_awaiting_payment} color="text-accent" />
            <StatCard label="Enrolled This Month"      value={stats?.enrolled_today}            color="text-success" />
            <StatCard label="Total This Month"         value={stats?.total_this_month}          />
          </div>

          {stats?.by_status && (
            <Card header={<h2 className="font-semibold text-gray-900">By Status</h2>}>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:grid-cols-3">
                {Object.entries(stats.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between py-1 border-b border-gray-100">
                    <span className="text-gray-600 capitalize">{status.replace(/_/g, ' ').toLowerCase()}</span>
                    <span className="font-semibold text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </AdminLayout>
  )
}
