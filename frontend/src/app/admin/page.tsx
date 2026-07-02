'use client'

import AdminLayout from '@/components/layout/AdminLayout'
import PageHeader from '@/components/ui/PageHeader'
import Card from '@/components/ui/Card'
import Spinner from '@/components/ui/Spinner'
import { useDashboardStats } from '@/hooks/useApplications'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
} from 'recharts'

// ── palette ──────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<string, string> = {
  SUBMITTED:          '#F5A623',
  UNDER_REVIEW:       '#2D5AA0',
  MORE_INFO_REQUESTED:'#8B5CF6',
  APPROVED:           '#16A34A',
  PAYMENT_PENDING:    '#D97706',
  PAYMENT_CONFIRMED:  '#0EA5E9',
  ENROLLED:           '#1B3A6B',
  REJECTED:           '#DC2626',
  DRAFT:              '#9CA3AF',
  WITHDRAWN:          '#6B7280',
}

const STATUS_LABEL: Record<string, string> = {
  SUBMITTED:           'Submitted',
  UNDER_REVIEW:        'Under Review',
  MORE_INFO_REQUESTED: 'More Info',
  APPROVED:            'Approved',
  PAYMENT_PENDING:     'Pay Pending',
  PAYMENT_CONFIRMED:   'Pay Confirmed',
  ENROLLED:            'Enrolled',
  REJECTED:            'Rejected',
  DRAFT:               'Draft',
  WITHDRAWN:           'Withdrawn',
}

// ── stat card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, color = 'text-primary', sub }:
  { label: string; value: number | undefined; color?: string; sub?: string }) {
  return (
    <Card className="text-center py-5">
      <p className={`text-4xl font-bold ${color}`}>{value ?? '—'}</p>
      <p className="mt-1 text-sm font-medium text-gray-700">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </Card>
  )
}

// ── custom tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: {
  active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-gray-100 bg-white shadow-lg px-3 py-2 text-sm">
      {label && <p className="font-semibold text-gray-700 mb-1">{label}</p>}
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

// ── page ──────────────────────────────────────────────────────────────────────

export default function AdminDashboardPage() {
  const { data: stats, isLoading } = useDashboardStats()

  const pieData = Object.entries(stats?.by_status ?? {})
    .filter(([, v]) => (v ?? 0) > 0)
    .map(([status, count]) => ({
      name: STATUS_LABEL[status] ?? status,
      value: count ?? 0,
      color: STATUS_COLORS[status] ?? '#9CA3AF',
    }))

  return (
    <AdminLayout>
      <PageHeader title="Reviewer Dashboard" subtitle="Application pipeline at a glance." />

      {isLoading && (
        <div className="flex justify-center py-20">
          <Spinner size="lg" className="text-primary" />
        </div>
      )}

      {!isLoading && (
        <div className="space-y-6">

          {/* ── KPI strip ── */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard
              label="Pending Review"
              value={stats?.pending_review}
              color="text-yellow-600"
              sub="awaiting assignment"
            />
            <StatCard
              label="Under Review"
              value={stats?.under_review}
              color="text-primary-light"
              sub="currently being assessed"
            />
            <StatCard
              label="Awaiting Payment"
              value={stats?.approved_awaiting_payment}
              color="text-accent"
              sub="approved, not yet paid"
            />
            <StatCard
              label="Enrolled This Month"
              value={stats?.enrolled_today}
              color="text-success"
              sub={`of ${stats?.total_this_month ?? 0} total`}
            />
          </div>

          {/* ── charts row ── */}
          <div className="grid gap-6 lg:grid-cols-5">

            {/* Donut — by status (spans 2 cols) */}
            <Card
              header={<h2 className="font-semibold text-gray-900">Applications by Status</h2>}
              className="lg:col-span-2"
            >
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      formatter={(v) => <span className="text-xs text-gray-600">{v}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Bar — by course (spans 3 cols) */}
            <Card
              header={<h2 className="font-semibold text-gray-900">Applications by Course</h2>}
              className="lg:col-span-3"
            >
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={stats?.by_course ?? []}
                    margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
                    layout="vertical"
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F3F4F6" />
                    <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <YAxis
                      type="category"
                      dataKey="course"
                      width={160}
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v: string) => v.length > 22 ? v.slice(0, 22) + '…' : v}
                    />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F9FAFB' }} />
                    <Bar dataKey="count" name="Applications" fill="#1B3A6B" radius={[0, 4, 4, 0]} barSize={18} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* ── Weekly submission trend ── */}
          <Card header={<h2 className="font-semibold text-gray-900">Submissions — Last 7 Days</h2>}>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={stats?.weekly_trend ?? []}
                  margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="subGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#1B3A6B" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#1B3A6B" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="submissions"
                    name="Submissions"
                    stroke="#1B3A6B"
                    strokeWidth={2}
                    fill="url(#subGrad)"
                    dot={{ r: 4, fill: '#1B3A6B', strokeWidth: 0 }}
                    activeDot={{ r: 5 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

        </div>
      )}
    </AdminLayout>
  )
}
