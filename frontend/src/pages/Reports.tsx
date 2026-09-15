import {
  AlertCircle,
  BarChart3,
  Calendar,
  ChevronLeft,
  Database,
  Download,
  FileSpreadsheet,
  FileText,
  Layers,
  Plus,
  Printer,
  RefreshCw,
  Search,
  Sparkles,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { UniversalReportRenderer } from '../components/report/UniversalReportRenderer'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { PageHeader } from '../components/ui/PageHeader'
import { reportService } from '../services/reportService'
import type { ReportResponse, ReportSummaryItem } from '../types/report'

// Domain color/icon mapping
const domainStyles: Record<string, { color: string; bg: string; border: string; icon: typeof BarChart3 }> = {
  hr: { color: 'text-violet-600', bg: 'bg-violet-50', border: 'border-violet-200', icon: Layers },
  sales: { color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', icon: BarChart3 },
  finance: { color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', icon: Database },
  general: { color: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200', icon: FileText },
}

function getDomainStyle(domain: string) {
  return domainStyles[domain?.toLowerCase()] || domainStyles.general
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Recently'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return 'Recently'
    return d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return 'Recently'
  }
}

export default function Reports() {
  const { reportId: pathReportId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [reportHistory, setReportHistory] = useState<ReportSummaryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const activeReportId = pathReportId || searchParams.get('reportId')
  const paramDatasetId = searchParams.get('datasetId')

  // ── List Mode: fetch all reports ──
  const fetchHistory = async () => {
    try {
      const history = await reportService.listReports()
      setReportHistory(history)
    } catch {
      // Ignore background list failure
    }
  }

  // ── Detail Mode: load or generate a specific report ──
  const loadOrGenerateReport = async () => {
    setError(null)
    setLoading(true)

    try {
      // 1. If explicit reportId, load it
      if (activeReportId) {
        const loaded = await reportService.getReport(activeReportId)
        setReport(loaded)
        setLoading(false)
        return
      }

      // 2. If datasetId param, generate report
      let targetDatasetId = paramDatasetId
      let targetFilename = 'dataset.csv'
      let mappings: Array<Record<string, unknown>> | undefined

      if (!targetDatasetId) {
        const latestUpload = sessionStorage.getItem('ai_backoffice_latest_upload')
        if (latestUpload) {
          try {
            const parsed = JSON.parse(latestUpload)
            targetDatasetId = parsed.uploadId
            targetFilename = parsed.fileName || targetFilename
          } catch {
            // Ignore parse error
          }
        }
      }

      const savedMappings = sessionStorage.getItem('ai_backoffice_mappings')
      if (savedMappings) {
        try {
          mappings = JSON.parse(savedMappings)
        } catch {
          // Ignore
        }
      }

      if (!targetDatasetId) {
        // No report to load, no dataset to generate — show list view
        setReport(null)
        setLoading(false)
        return
      }

      // 3. Generate report
      setGenerating(true)
      const generated = await reportService.generateReport(
        targetDatasetId,
        targetFilename,
        mappings
      )
      setReport(generated)
      setSearchParams({ reportId: generated.report_id })
      await fetchHistory()
    } catch (err: any) {
      console.error('Failed to load/generate report:', err)
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to generate deterministic intelligence report.'
      )
    } finally {
      setLoading(false)
      setGenerating(false)
    }
  }

  useEffect(() => {
    void fetchHistory()
    if (activeReportId || paramDatasetId) {
      void loadOrGenerateReport()
    } else {
      setLoading(false)
    }
  }, [activeReportId, paramDatasetId])

  const handleExportJson = () => {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.report_id}_${report.domain}_report.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleSelectReport = (repId: string) => {
    setSearchParams({ reportId: repId })
  }

  const handleBackToList = () => {
    setReport(null)
    setSearchParams({})
  }

  // ── Filter reports by search ──
  const filteredReports = reportHistory.filter((r) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      r.title?.toLowerCase().includes(q) ||
      (r.domain || '').toLowerCase().includes(q) ||
      r.report_id?.toLowerCase().includes(q)
    )
  })

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ► DETAIL VIEW — A specific report is loaded
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (activeReportId || report) {
    return (
      <div className="space-y-8 animate-fade-in pb-12">
        {/* Top Header with back button */}
        <PageHeader
          eyebrow="Universal Intelligence Engine"
          title="Executive Intelligence Report"
          description="Autonomous, deterministic C-suite reporting synthesized directly from raw operational data."
          actions={
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={handleBackToList}>
                <ChevronLeft className="mr-1.5 h-3.5 w-3.5" />
                All Reports
              </Button>
              {report && (
                <>
                  <Button variant="secondary" size="sm" onClick={handleExportJson}>
                    <Download className="mr-1.5 h-3.5 w-3.5" />
                    Export JSON
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => window.print()}>
                    <Printer className="mr-1.5 h-3.5 w-3.5" />
                    Print / PDF
                  </Button>
                </>
              )}
            </div>
          }
        />

        {/* Loading */}
        {loading && (
          <Card className="border-slate-200/80 shadow-sm">
            <CardContent className="py-24 text-center space-y-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-50 text-brand-600 animate-spin border border-brand-100 shadow-sm">
                <RefreshCw className="h-8 w-8" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-slate-900">
                  {generating ? 'Composing Autonomous Business Intelligence...' : 'Loading Executive Report...'}
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  Executing statistical profiling, evaluating z-scores and IQR distributions, identifying domain capabilities.
                </p>
              </div>
              <div className="flex items-center justify-center gap-2 pt-2">
                <span className="h-2 w-2 rounded-full bg-brand-600 animate-pulse" />
                <span className="h-2 w-2 rounded-full bg-brand-400 animate-pulse delay-75" />
                <span className="h-2 w-2 rounded-full bg-brand-200 animate-pulse delay-150" />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {error && !loading && (
          <Card className="border-red-200 bg-red-50/50 shadow-sm">
            <CardContent className="py-10 text-center space-y-4">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-red-600">
                <AlertCircle className="h-7 w-7" />
              </div>
              <div className="space-y-1 max-w-md mx-auto">
                <h3 className="text-base font-bold text-red-900">Unable to Synthesize Report</h3>
                <p className="text-xs text-red-700 leading-relaxed">{error}</p>
              </div>
              <div className="pt-2 flex items-center justify-center gap-3">
                <Button variant="secondary" size="sm" onClick={() => void loadOrGenerateReport()}>
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                  Retry Synthesis
                </Button>
                <Button variant="secondary" size="sm" onClick={handleBackToList}>
                  Back to Reports
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Report Render */}
        {!loading && !error && report && (
          <ErrorBoundary fallbackTitle="Report Section Rendering">
            <UniversalReportRenderer
              report={report}
              onExportJson={handleExportJson}
              onPrint={() => window.print()}
            />
          </ErrorBoundary>
        )}
      </div>
    )
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ► LIST VIEW — Browse all reports
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Header */}
      <PageHeader
        eyebrow="Universal Intelligence Engine"
        title="Executive Intelligence Reports"
        description="Autonomous, deterministic C-suite reporting synthesized directly from raw operational data with mathematical precision."
        actions={
          <Link to="/upload?intent=report_generation">
            <Button variant="default" size="sm" className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25">
              <Plus className="mr-1.5 h-4 w-4" />
              Audit New Dataset
            </Button>
          </Link>
        }
      />

      {/* Hero Stats Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl shadow-slate-900/10">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-purple-500/15 blur-3xl" />

        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 rounded-full border border-brand-400/30 bg-brand-500/20 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-brand-300">
                <Sparkles className="h-3 w-3" />
                Intelligence Archive
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Report Intelligence Library
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Browse, search, and access all previously generated executive intelligence reports.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 w-full sm:w-auto">
            <div className="rounded-xl bg-white/5 backdrop-blur-sm p-3 min-w-[100px]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-brand-300">Total Reports</p>
              <p className="text-2xl font-black text-white mt-0.5">{reportHistory.length}</p>
            </div>
            <div className="rounded-xl bg-white/5 backdrop-blur-sm p-3 min-w-[100px]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-300">Domains</p>
              <p className="text-2xl font-black text-emerald-400 mt-0.5">
                {new Set(reportHistory.map(r => (r.domain || 'general').toLowerCase())).size}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      {reportHistory.length > 0 && (
        <div className="relative">
          <Search className="absolute left-4 top-3.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search reports by title, domain, or ID..."
            className="w-full rounded-2xl border border-slate-200 bg-white pl-11 pr-4 py-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-56 rounded-2xl border border-slate-200 bg-slate-50 animate-pulse" />
          ))}
        </div>
      )}

      {/* Report Cards Grid */}
      {!loading && filteredReports.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredReports.map((r) => {
            const style = getDomainStyle(r.domain)
            const Icon = style.icon
            return (
              <button
                key={r.report_id}
                type="button"
                onClick={() => handleSelectReport(r.report_id)}
                className="group relative text-left overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:border-brand-300 hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-brand-400"
              >
                {/* Decorative gradient corner */}
                <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-brand-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100 blur-2xl" />

                <div className="relative z-10 space-y-4">
                  {/* Domain badge + icon */}
                  <div className="flex items-center justify-between">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${style.bg} ${style.color} transition-transform duration-200 group-hover:scale-110`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className={`rounded-full border ${style.border} ${style.bg} px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${style.color}`}>
                      {(r.domain || 'general').toUpperCase()}
                    </span>
                  </div>

                  {/* Title */}
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 line-clamp-2 group-hover:text-brand-700 transition-colors">
                      {r.title || 'Untitled Report'}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono truncate">
                      ID: {r.report_id}
                    </p>
                  </div>

                  {/* Metadata chips */}
                  <div className="flex flex-wrap items-center gap-2 text-[11px]">
                    <span className="flex items-center gap-1 text-slate-500">
                      <FileSpreadsheet className="h-3 w-3" />
                      {(r.row_count ?? 0).toLocaleString()} rows
                    </span>
                    <span className="h-3 w-px bg-slate-200" />
                    <span className="flex items-center gap-1 text-slate-500">
                      <Calendar className="h-3 w-3" />
                      {formatDate(r.generated_at)}
                    </span>
                  </div>
                </div>

                {/* Hover arrow indicator */}
                <div className="absolute right-4 bottom-4 opacity-0 translate-x-2 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <ChevronLeft className="h-4 w-4 rotate-180" />
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* Empty State */}
      {!loading && reportHistory.length === 0 && (
        <Card className="overflow-hidden border-slate-200/80 shadow-sm">
          <div className="relative px-6 py-20 text-center sm:px-12 sm:py-24">
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-brand-50/40 to-transparent" />
            <div className="relative max-w-md mx-auto space-y-5">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-brand-50 text-brand-600 shadow-sm border border-brand-100">
                <FileText className="h-10 w-10" />
              </div>
              <div className="space-y-1.5">
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">No Executive Reports Yet</h2>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Upload any operational CSV or Excel dataset — whether workforce talent metrics, sales journals,
                  or cost ledgers — to immediately generate a deterministic, C-suite grade executive intelligence brief.
                </p>
              </div>
              <div className="pt-2 flex items-center justify-center">
                <Link to="/upload?intent=report_generation">
                  <Button size="lg" className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25">
                    <FileSpreadsheet className="mr-2 h-4 w-4" />
                    Upload Operational Dataset
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* No search results */}
      {!loading && reportHistory.length > 0 && filteredReports.length === 0 && searchQuery && (
        <div className="text-center py-12">
          <Search className="h-8 w-8 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700">No reports matching "{searchQuery}"</h3>
          <p className="text-xs text-slate-500 mt-1">Try a different search term or clear the filter.</p>
        </div>
      )}
    </div>
  )
}
