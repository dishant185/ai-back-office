import { cn } from '../../lib/utils'

interface ProfileAvatarProps {
  name?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ProfileAvatar({ name, size = 'md', className }: ProfileAvatarProps) {
  const initials = name
    ? name
        .trim()
        .split(/\s+/)
        .map((w) => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'DK'

  const sizeClasses = {
    sm: 'h-6 w-6 text-[10px]',
    md: 'h-8 w-8 text-xs', // 32px x 32px
    lg: 'h-10 w-10 text-sm',
  }

  return (
    <div
      className={cn(
        'inline-flex shrink-0 items-center justify-center font-mono font-bold select-none text-white transition-opacity',
        // Specific requirement: square avatar, border-radius 4px, background #176B50
        'rounded-[4px] bg-[#176B50]',
        sizeClasses[size],
        className
      )}
      aria-hidden="true"
    >
      <span>{initials}</span>
    </div>
  )
}
