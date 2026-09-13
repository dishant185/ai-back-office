import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { cn } from '../../lib/utils'

type ButtonVariant = 'default' | 'secondary' | 'ghost' | 'outline' | 'danger'
type ButtonSize = 'default' | 'sm' | 'lg' | 'icon'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: ReactNode
}

export function Button({
  className,
  variant = 'default',
  size = 'default',
  children,
  ...props
}: ButtonProps) {
  const variantClasses: Record<ButtonVariant, string> = {
    default:
      'gradient-brand text-white shadow-md shadow-brand-500/25 hover:shadow-lg hover:shadow-brand-500/30 hover:brightness-110 active:scale-[0.98]',
    secondary:
      'bg-white text-slate-700 border border-slate-200 shadow-sm hover:bg-slate-50 hover:border-slate-300 active:scale-[0.98]',
    ghost: 'bg-transparent text-slate-600 hover:bg-slate-100/80 hover:text-slate-900',
    outline:
      'border border-brand-200 bg-brand-50/50 text-brand-700 hover:bg-brand-50 hover:border-brand-300',
    danger:
      'bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 active:scale-[0.98]',
  }

  const sizeClasses: Record<ButtonSize, string> = {
    default: 'h-10 px-4 py-2 text-sm',
    sm: 'h-8 px-3 text-xs',
    lg: 'h-11 px-6 text-sm',
    icon: 'h-9 w-9 p-0',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/40 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
