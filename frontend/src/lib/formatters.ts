/**
 * Centralized formatting utilities for enterprise analytics display.
 * Avoids ad-hoc number formatting and guarantees consistent localization.
 */

export function formatNumber(value: number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined || isNaN(value)) return '0'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatCurrency(
  value: number | null | undefined,
  currency = 'USD',
  compact = false
): string {
  if (value === null || value === undefined || isNaN(value)) return '$0'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 2,
  }).format(value)
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || isNaN(value)) return '0%'
  const numeric = typeof value === 'number' ? value : Number(value)
  // If value is between 0 and 1, convert to 0-100%
  const pct = Math.abs(numeric) <= 1 && numeric !== 0 ? numeric * 100 : numeric
  return `${pct.toFixed(decimals)}%`
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** index
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`
}

export function formatDate(
  dateStr: string | Date | null | undefined,
  style: 'short' | 'medium' | 'long' = 'medium'
): string {
  if (!dateStr) return '—'
  try {
    const d = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
    if (isNaN(d.getTime())) return '—'
    if (style === 'short') {
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
    if (style === 'long') {
      return d.toLocaleString('en-US', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    }
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return '—'
  }
}

export function timeAgo(isoString: string | null | undefined): string {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
    const diffHrs = Math.floor(diffMins / 60)
    if (diffHrs < 24) return `${diffHrs} hour${diffHrs > 1 ? 's' : ''} ago`
    const diffDays = Math.floor(diffHrs / 24)
    if (diffDays === 1) return 'Yesterday'
    return `${diffDays} days ago`
  } catch {
    return ''
  }
}
