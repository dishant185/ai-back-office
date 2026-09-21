import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { cn } from '../../lib/utils'

type ButtonVariant = 'default' | 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'
type ButtonSize = 'default' | 'sm' | 'md' | 'lg' | 'icon'

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
      'bg-novera-green text-white hover:bg-novera-green-bright active:opacity-90 font-medium transition-colors',
    primary:
      'bg-novera-green text-white hover:bg-novera-green-bright active:opacity-90 font-medium transition-colors',
    secondary:
      'bg-novera-paper-sheet text-novera-ink border border-novera-rule hover:bg-novera-paper active:bg-novera-paper-sunken font-medium transition-colors',
    ghost:
      'bg-transparent text-novera-secondary hover:bg-novera-paper-sunken hover:text-novera-ink transition-colors',
    outline:
      'border border-novera-rule bg-transparent text-novera-ink hover:bg-novera-paper transition-colors',
    danger:
      'bg-novera-flag text-white hover:opacity-90 active:opacity-80 transition-colors',
  }

  const sizeClasses: Record<ButtonSize, string> = {
    default: 'h-9 px-3.5 py-1.5 text-xs',
    md: 'h-9 px-3.5 py-1.5 text-xs',
    sm: 'h-7 px-2.5 py-1 text-xs',
    lg: 'h-10 px-4 py-2 text-sm',
    icon: 'h-8 w-8 p-0',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-[2px] font-sans transition-all duration-150 cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-novera-green focus-visible:ring-offset-1',
        'disabled:pointer-events-none disabled:opacity-40 select-none',
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
