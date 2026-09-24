import React, { forwardRef } from 'react'
import { cn } from '../../lib/utils'

export interface AuthInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  hint?: string
}

export const AuthInput = forwardRef<HTMLInputElement, AuthInputProps>(
  ({ id, label, error, hint, className, required, ...props }, ref) => {
    const inputId = id || `input-${label.toLowerCase().replace(/\s+/g, '-')}`
    const errorId = `${inputId}-error`
    const hintId = `${inputId}-hint`

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
          {hint && (
            <span id={hintId} className="text-[11px] text-[#66716C] dark:text-[#AAB5AF]">
              {hint}
            </span>
          )}
        </div>

        <input
          ref={ref}
          id={inputId}
          required={required}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : hint ? hintId : undefined}
          className={cn(
            'h-11 w-full rounded-[2px] border px-3 text-sm transition-colors outline-none',
            'bg-white dark:bg-[#1B2528] text-[#11181B] dark:text-[#EEF2EE]',
            'placeholder:text-[#66716C]/60 dark:placeholder:text-[#AAB5AF]/50',
            error
              ? 'border-[#B33A3A] focus:border-[#B33A3A] focus:ring-1 focus:ring-[#B33A3A]'
              : 'border-[#C7CEC8] dark:border-[#2B3538] focus:border-[#176B50] dark:focus:border-[#4FAF87] focus:ring-1 focus:ring-[#176B50] dark:focus:ring-[#4FAF87]',
            className
          )}
          {...props}
        />

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

AuthInput.displayName = 'AuthInput'
