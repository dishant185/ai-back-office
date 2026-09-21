import {
  AlertTriangle,
  Calendar,
  Download,
  FileSpreadsheet,
  Loader2,
  Printer,
  RefreshCw,
  Sparkles,
} from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

interface ReportHeaderProps {
  title: string
  subtitle: string
  domain: string
  rowCount: number
  columnCount: number
  generatedAt: string
  datasetVersion?: number
  isStale?: boolean
  status?: string
  onDownloadPdf?: () => void
  isDownloadingPdf?: boolean
  onRegenerate?: () => void
  isRegenerating?: boolean
  onAiSummary?: () => void
  isGeneratingAi?: boolean
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
  datasetVersion = 1,
  isStale = false,
  status = 'completed',
  onDownloadPdf,
  isDownloadingPdf = false,
  onRegenerate,
  isRegenerating = false,
  onAiSummary,
  isGeneratingAi = false,
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
    <div className="space-y-3">
      {/* Stale Warning Banner */}
      {isStale && (
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50/90 px-4 py-3 text-xs font-semibold text-amber-900 shadow-sm print:hidden">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />
            <span>
              Dataset updated — this report is based on version {datasetVersion}. A newer dataset version is available.
            </span>
          </div>
          {onRegenerate && (
            <Button
              size="sm"
              variant="outline"
              onClick={onRegenerate}
              disabled={isRegenerating}
              className="h-7 text-[11px] font-bold border-amber-300 bg-white hover:bg-amber-100 text-amber-900"
            >
              {isRegenerating ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="mr-1.5 h-3.5 w-3.5" />}
              Regenerate on Latest Data
            </Button>
          )}
        </div>
      )}

      {/* Main Header */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8">
        <div className="pointer-events-none absolute right-0 top-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-brand-500/5 blur-3xl" />
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="brand" dot>
                <Sparkles className="h-3 w-3 mr-1" />
                {(domain || 'MIS').toUpperCase()} REPORT
              </Badge>
              <Badge variant="info">
                <FileSpreadsheet className="h-3 w-3 mr-1" />
                {(rowCount ?? 0).toLocaleString()} Rows × {columnCount ?? 0} Columns
              </Badge>
              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-mono font-medium text-slate-600">
                v{datasetVersion}
              </span>
              {status === 'stale' && (
                <span className="rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-800">
                  Stale
                </span>
              )}
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

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5 print:hidden">
            {onAiSummary && (
              <Button
                variant="outline"
                size="sm"
                onClick={onAiSummary}
                disabled={isGeneratingAi}
                className="shadow-sm border-indigo-200 text-indigo-700 bg-indigo-50/50 hover:bg-indigo-100"
              >
                {isGeneratingAi ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin text-indigo-600" />
                ) : (
                  <Sparkles className="mr-1.5 h-4 w-4 text-indigo-600" />
                )}
                AI Summary
              </Button>
            )}

            {onDownloadPdf && (
              <Button
                variant="default"
                size="sm"
                onClick={onDownloadPdf}
                disabled={isDownloadingPdf}
                className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-sm shadow-brand-500/20"
              >
                {isDownloadingPdf ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-1.5 h-4 w-4" />
                )}
                Download PDF
              </Button>
            )}

            <Button
              variant="secondary"
              size="sm"
              onClick={onPrint || (() => window.print())}
              className="shadow-sm"
            >
              <Printer className="mr-1.5 h-4 w-4" />
              Print
            </Button>

            {onRegenerate && (
              <Button
                variant="secondary"
                size="sm"
                onClick={onRegenerate}
                disabled={isRegenerating}
                className="shadow-sm"
              >
                {isRegenerating ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-1.5 h-4 w-4" />
                )}
                Regenerate
              </Button>
            )}

            {onExportJson && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onExportJson}
                className="text-slate-500 hover:text-slate-700"
              >
                Export JSON
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
