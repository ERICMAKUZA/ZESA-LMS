import { clsx } from 'clsx'
import { type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  header?: ReactNode
  footer?: ReactNode
  className?: string
}

export default function Card({ children, header, footer, className }: CardProps) {
  return (
    <div className={clsx('rounded-lg border border-gray-200 bg-white shadow-sm', className)}>
      {header && <div className="border-b border-gray-200 px-6 py-4">{header}</div>}
      <div className="px-6 py-4">{children}</div>
      {footer && <div className="border-t border-gray-200 px-6 py-4">{footer}</div>}
    </div>
  )
}
