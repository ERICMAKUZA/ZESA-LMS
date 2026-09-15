import { forwardRef, useState, type InputHTMLAttributes } from 'react'
import { clsx } from 'clsx'
import { Eye, EyeOff } from 'lucide-react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helper?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helper, className, id, type, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
    const isPassword = type === 'password'
    const [isPasswordVisible, setIsPasswordVisible] = useState(false)

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <div className={clsx(isPassword && 'relative')}>
          <input
            ref={ref}
            id={inputId}
            type={isPassword && isPasswordVisible ? 'text' : type}
            className={clsx(
              'block w-full rounded-md border-gray-300 shadow-sm text-sm',
              'focus:border-primary focus:ring-primary',
              error && 'border-danger focus:border-danger focus:ring-danger',
              isPassword && 'pr-10',
              className,
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              aria-label={isPasswordVisible ? 'Hide password' : 'Show password'}
              aria-pressed={isPasswordVisible}
              onClick={() => setIsPasswordVisible((visible) => !visible)}
              className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
            >
              {isPasswordVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
        </div>
        {error && <p className="text-xs text-danger">{error}</p>}
        {!error && helper && <p className="text-xs text-gray-500">{helper}</p>}
      </div>
    )
  },
)

Input.displayName = 'Input'
export default Input
