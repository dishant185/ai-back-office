import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-novera-rule pb-5">
      <div className="space-y-1">
        {eyebrow && (
          <div className="flex items-center gap-1.5 text-xs font-mono text-novera-muted">
            <span className="h-1.5 w-1.5 rounded-[1px] bg-novera-green" />
            <span>{eyebrow}</span>
          </div>
        )}
        <h1 className="text-xl font-bold tracking-tight text-novera-ink sm:text-2xl font-sans">
          {title}
        </h1>
        {description && (
          <p className="max-w-3xl text-xs sm:text-sm leading-relaxed text-novera-secondary">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2 pt-1">{actions}</div>}
    </div>
  )
}
