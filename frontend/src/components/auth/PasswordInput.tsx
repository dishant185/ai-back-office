import { Eye, EyeOff } from 'lucide-react'
import React, { forwardRef, useState } from 'react'
import { cn } from '../../lib/utils'

export interface PasswordInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string
  error?: string
  hint?: React.ReactNode
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ id, label = 'Password', error, hint, className, required, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false)
    const inputId = id || `input-${label.toLowerCase().replace(/\s+/g, '-')}`
    const errorId = `${inputId}-error`

    return (
      <div className="flex flex-col gap-1.5 w-full">
        <div className="flex items-center justify-between">
          <label
            htmlFor={inputId}
            className="text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE]"
          >
            {label}
            {required && <span className="text-[#B33A3A] ml-0.5">*</span>}
          </label>
          {hint && <div>{hint}</div>}
        </div>

        <div className="relative flex items-center">
          <input
            ref={ref}
            id={inputId}
            type={showPassword ? 'text' : 'password'}
            required={required}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : undefined}
            className={cn(
              'h-11 w-full rounded-[2px] border pl-3 pr-10 text-sm transition-colors outline-none',
              'bg-white dark:bg-[#1B2528] text-[#11181B] dark:text-[#EEF2EE]',
              'placeholder:text-[#66716C]/60 dark:placeholder:text-[#AAB5AF]/50',
              error
                ? 'border-[#B33A3A] focus:border-[#B33A3A] focus:ring-1 focus:ring-[#B33A3A]'
                : 'border-[#C7CEC8] dark:border-[#2B3538] focus:border-[#176B50] dark:focus:border-[#4FAF87] focus:ring-1 focus:ring-[#176B50] dark:focus:ring-[#4FAF87]',
              className
            )}
            {...props}
          />
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            className="absolute right-2.5 flex h-7 w-7 items-center justify-center rounded-[2px] text-[#66716C] hover:text-[#11181B] dark:text-[#AAB5AF] dark:hover:text-white transition-colors cursor-pointer"
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" strokeWidth={1.8} />
            ) : (
              <Eye className="h-4 w-4" strokeWidth={1.8} />
            )}
          </button>
        </div>

        {error && (
          <p
            id={errorId}
            className="text-[11px] text-[#B33A3A] dark:text-[#D06161] flex items-center gap-1 font-medium"
          >
            <span>⚠</span>
            <span>{error}</span>
          </p>
        )}
      </div>
    )
  }
)

PasswordInput.displayName = 'PasswordInput'
