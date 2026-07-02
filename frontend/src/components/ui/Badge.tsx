import { clsx } from 'clsx'
import type { ApplicationStatus } from '@/types'

const statusConfig: Record<ApplicationStatus, { label: string; className: string }> = {
  DRAFT:               { label: 'Draft',               className: 'bg-gray-100 text-gray-700' },
  SUBMITTED:           { label: 'Submitted',           className: 'bg-blue-100 text-blue-700' },
  UNDER_REVIEW:        { label: 'Under Review',        className: 'bg-yellow-100 text-yellow-800' },
  MORE_INFO_REQUESTED: { label: 'More Info Needed',    className: 'bg-orange-100 text-orange-700' },
  APPROVED:            { label: 'Approved',            className: 'bg-green-100 text-green-700' },
  REJECTED:            { label: 'Rejected',            className: 'bg-red-100 text-red-700' },
  PAYMENT_PENDING:     { label: 'Payment Pending',     className: 'bg-orange-100 text-orange-800' },
  PAYMENT_CONFIRMED:   { label: 'Payment Confirmed',   className: 'bg-teal-100 text-teal-700' },
  ENROLLED:            { label: 'Enrolled',            className: 'bg-green-200 text-green-900' },
  DE_ENROLLED:         { label: 'De-enrolled',         className: 'bg-red-100 text-red-700' },
  CERTIFIED:           { label: 'Certified',           className: 'bg-purple-100 text-purple-700' },
}

interface BadgeProps {
  status: ApplicationStatus
  className?: string
}

export default function Badge({ status, className }: BadgeProps) {
  const { label, className: colorClass } = statusConfig[status] ?? {
    label: status,
    className: 'bg-gray-100 text-gray-700',
  }
  return (
    <span className={clsx('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', colorClass, className)}>
      {label}
    </span>
  )
}
