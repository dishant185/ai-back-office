import { useTheme } from '../../context/ThemeContext'
import { cn } from '../../lib/utils'

export type LogoVariant = 'full' | 'compact' | 'mark'
export type LogoSize = 'sm' | 'md' | 'lg'
export type LogoTheme = 'light' | 'dark' | 'auto'

export interface NoveraLogoProps {
  variant?: LogoVariant
  size?: LogoSize
  theme?: LogoTheme
  className?: string
  priority?: boolean
}

// Preset sizing definitions (height-constrained, aspect-ratio preserved with object-fit: contain)
const SIZE_STYLES: Record<LogoVariant, Record<LogoSize, string>> = {
  full: {
    sm: 'h-10 w-auto max-w-[170px]',
    md: 'h-16 w-auto max-w-[260px]',
    lg: 'h-24 w-auto max-w-[360px]',
  },
  compact: {
    sm: 'h-6 w-auto max-w-[130px]',
    md: 'h-8 w-auto max-w-[180px]',
    lg: 'h-10 w-auto max-w-[230px]',
  },
  mark: {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  },
}

export function NoveraLogo({
  variant = 'compact',
  size = 'md',
  theme = 'auto',
  className,
}: NoveraLogoProps) {
  const { resolvedTheme } = useTheme()

  // Determine whether to use dark surface assets (white lettering) or light surface assets (dark lettering)
  const isDarkSurface =
    theme === 'dark' ? true : theme === 'light' ? false : resolvedTheme === 'dark'

  let src = '/novera-compact.png'

  if (variant === 'mark') {
    src = '/novera-mark.png'
  } else if (variant === 'full') {
    src = isDarkSurface ? '/novera-full-light.png' : '/novera-full.png'
  } else {
    // compact
    src = isDarkSurface ? '/novera-compact-light.png' : '/novera-compact.png'
  }

  return (
    <img
      src={src}
      alt="Novera"
      className={cn(
        'select-none object-contain transition-opacity duration-150',
        SIZE_STYLES[variant][size],
        className
      )}
      loading="eager"
      decoding="async"
    />
  )
}
