import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { clsx } from 'clsx'
import Spinner from './Spinner'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const base =
  'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'

const variants = {
  primary: 'bg-primary text-white hover:bg-primary-light focus-visible:ring-primary',
  secondary: 'bg-accent text-white hover:bg-accent-light focus-visible:ring-accent',
  outline: 'border border-primary text-primary hover:bg-primary hover:text-white focus-visible:ring-primary',
  danger: 'bg-danger text-white hover:bg-red-700 focus-visible:ring-danger',
  ghost: 'text-primary hover:bg-primary/10 focus-visible:ring-primary',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, children, disabled, className, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={clsx(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  ),
)

Button.displayName = 'Button'
export default Button
