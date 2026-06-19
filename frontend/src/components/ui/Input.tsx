import { forwardRef, type InputHTMLAttributes } from 'react'
import { clsx } from 'clsx'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helper?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helper, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'block w-full rounded-md border-gray-300 shadow-sm text-sm',
            'focus:border-primary focus:ring-primary',
            error && 'border-danger focus:border-danger focus:ring-danger',
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
        {!error && helper && <p className="text-xs text-gray-500">{helper}</p>}
      </div>
    )
  },
)

Input.displayName = 'Input'
export default Input
