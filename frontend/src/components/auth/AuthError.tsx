import { AlertCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

interface AuthErrorProps {
  message?: string
  className?: string
  id?: string
}

export function AuthError({ message, className, id = 'auth-error' }: AuthErrorProps) {
  if (!message) return null

  return (
    <div
      id={id}
      role="alert"
      aria-live="polite"
      className={cn(
        'flex items-start gap-2.5 rounded-[2px] border border-[#B33A3A]/30 bg-[#B33A3A]/[0.08] p-3 text-xs text-[#B33A3A] dark:text-[#D06161]',
        className
      )}
    >
      <AlertCircle className="h-4 w-4 shrink-0 text-[#B33A3A] dark:text-[#D06161] mt-0.5" />
      <div className="flex-1">
        <p className="font-semibold">Sign-in failed</p>
        <p className="text-[11px] opacity-90 mt-0.5">{message}</p>
      </div>
    </div>
  )
}
