import { Loader2 } from 'lucide-react'
import React from 'react'
import { cn } from '../../lib/utils'

interface AuthSubmitButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
  loadingText?: string
  children: React.ReactNode
}

export function AuthSubmitButton({
  loading = false,
  loadingText = 'Signing in...',
  children,
  className,
  disabled,
  ...props
}: AuthSubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={disabled || loading}
      className={cn(
        'group flex h-11 w-full items-center justify-center gap-2 rounded-[2px] px-4 font-sans text-sm font-semibold text-white transition-colors cursor-pointer select-none',
        // Novera Green #176B50, Hover #2D8A68
        'bg-[#176B50] hover:bg-[#2D8A68] active:bg-[#135540]',
        'focus:outline-none focus:ring-2 focus:ring-[#176B50] focus:ring-offset-2 dark:focus:ring-offset-[#141C1F]',
        'disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-[#176B50]',
        className
      )}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin text-white/80" />
          <span>{loadingText}</span>
        </>
      ) : (
        children
      )}
    </button>
  )
}
