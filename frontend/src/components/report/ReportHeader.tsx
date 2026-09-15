import { Calendar, Download, FileSpreadsheet, Printer, Sparkles } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

interface ReportHeaderProps {
  title: string
  subtitle: string
  domain: string
  rowCount: number
  columnCount: number
  generatedAt: string
  onExportJson?: () => void
  onPrint?: () => void
}

export function ReportHeader({
  title,
  subtitle,
  domain,
  rowCount,
  columnCount,
  generatedAt,
  onExportJson,
  onPrint,
}: ReportHeaderProps) {
  let formattedDate = 'Recently'
  if (generatedAt) {
    try {
      const d = new Date(generatedAt)
      if (!isNaN(d.getTime())) {
        formattedDate = d.toLocaleString('en-US', {
          dateStyle: 'medium',
          timeStyle: 'short',
        })
      }
    } catch {
      formattedDate = 'Recently'
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
      <div className="pointer-events-none absolute right-0 top-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-brand-500/5 blur-3xl" />
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="brand" dot>
              <Sparkles className="h-3 w-3 mr-1" />
              {(domain || 'HR').toUpperCase()} INTELLIGENCE
            </Badge>
            <Badge variant="info">
              <FileSpreadsheet className="h-3 w-3 mr-1" />
              {(rowCount ?? 0).toLocaleString()} Rows × {columnCount ?? 0} Columns
            </Badge>
            <span className="flex items-center text-xs text-slate-400">
              <Calendar className="mr-1 h-3.5 w-3.5" />
              {formattedDate}
            </span>
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              {title}
            </h1>
            <p className="mt-1 text-sm text-slate-500 max-w-2xl">{subtitle}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={onPrint || (() => window.print())}
            className="shadow-sm"
          >
            <Printer className="mr-1.5 h-4 w-4" />
            Print / PDF
          </Button>
          {onExportJson && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onExportJson}
              className="shadow-sm"
            >
              <Download className="mr-1.5 h-4 w-4" />
              Export JSON
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
