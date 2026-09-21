import {
  BarChart3,
  Calendar,
  ChevronLeft,
  Database,
  Download,
  FileSpreadsheet,
  FileText,
  Layers,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { UniversalReportRenderer } from '../components/report/UniversalReportRenderer'
import { ReportGenerateModal } from '../components/report/ReportGenerateModal'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { CardSkeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { PageHeader } from '../components/ui/PageHeader'
import api from '../services/api'
import { reportService } from '../services/reportService'
import type { ReportResponse, ReportSummaryItem } from '../types/report'

// Domain color/icon mapping
const domainStyles: Record<string, { color: string; bg: string; border: string; icon: typeof BarChart3 }> = {
  hr: { color: 'text-violet-600', bg: 'bg-violet-50', border: 'border-violet-200', icon: Layers },
  sales: { color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', icon: BarChart3 },
  finance: { color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', icon: Database },
  inventory: { color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', icon: Database },
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
  const [datasetList, setDatasetList] = useState<Array<{ id: string; name: string; profile?: string; row_count?: number }>>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Modal & Action States
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isGeneratingAi, setIsGeneratingAi] = useState(false)
  const [aiSummaryResult, setAiSummaryResult] = useState<Record<string, any> | null>(null)

  const activeReportId = pathReportId || searchParams.get('reportId')
  const paramDatasetId = searchParams.get('datasetId')

  // ── Fetch datasets for modal ──
  const fetchDatasets = async () => {
    try {
      const resp = await api.get<any[]>('/api/v1/datasets')
      if (Array.isArray(resp.data)) {
        setDatasetList(
          resp.data.map((d) => ({
            id: d.dataset_id || d.upload_id || d.id,
            name: d.filename || d.file_name || d.name || d.dataset_id,
            profile: d.profile || 'generic',
            row_count: d.row_count || d.summary?.rows,
          }))
        )
      }
    } catch {
      // Fallback from session storage
      const stored = sessionStorage.getItem('ai_backoffice_latest_upload')
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          setDatasetList([{ id: parsed.uploadId, name: parsed.fileName || 'Current Dataset' }])
        } catch {
          // ignore
        }
      }
    }
  }

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
    setAiSummaryResult(null)

    try {
      // 1. If explicit reportId, load it
      if (activeReportId) {
        const loaded = await reportService.getReport(activeReportId)
        setReport(loaded)
        if ((loaded as any).ai_summary) {
          setAiSummaryResult((loaded as any).ai_summary)
        }
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
      const generated = await reportService.generateReport(targetDatasetId, {
        filename: targetFilename,
        mappings,
      })
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
    void fetchDatasets()
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

  const handleDownloadPdf = async () => {
    if (!report) return
    setIsDownloadingPdf(true)
    try {
      const cleanTitle = (report.title || 'report').replace(/[^a-zA-Z0-9_-]/g, '_')
      await reportService.downloadPdf(report.report_id, `${cleanTitle}_v${report.dataset_version || 1}.pdf`)
    } catch (err) {
      console.error('PDF download error:', err)
      alert('Failed to generate PDF. Please try again.')
    } finally {
      setIsDownloadingPdf(false)
    }
  }

  const handleRegenerate = async () => {
    if (!report) return
    setIsRegenerating(true)
    try {
      const regenerated = await reportService.regenerateReport(report.report_id)
      setReport(regenerated)
      setAiSummaryResult(null)
      await fetchHistory()
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to regenerate report.')
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleAiSummary = async (options?: { regenerate?: boolean }) => {
    if (!report) return
    setIsGeneratingAi(true)
    try {
      const isRegen = options?.regenerate ?? Boolean(aiSummaryResult)
      const summary = await reportService.generateAiSummary(report.report_id, { regenerate: isRegen })
      setAiSummaryResult(summary)
    } catch (err) {
      console.error('AI summary error:', err)
    } finally {
      setIsGeneratingAi(false)
    }
  }

  const handleDeleteReport = async (e: React.MouseEvent, reportId: string) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this report?')) return
    try {
      await reportService.deleteReport(reportId)
      await fetchHistory()
      if (activeReportId === reportId) {
        handleBackToList()
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to delete report.')
    }
  }

  const handleSelectReport = (repId: string) => {
    setSearchParams({ reportId: repId })
  }

  const handleBackToList = () => {
    setReport(null)
    setSearchParams({})
  }

  const handleSelectAutonomousModule = async (reportType: string) => {
    if (!report) return
    setGenerating(true)
    setError(null)
    try {
      const generated = await reportService.generateReport(report.dataset_id, {
        reportType,
        filters: report.filters || {},
      })
      setReport(generated)
      setAiSummaryResult(null)
      setSearchParams({ reportId: generated.report_id })
      await fetchHistory()
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to switch report module.')
    } finally {
      setGenerating(false)
    }
  }

  const handleGenerateFromModal = async (datasetId: string, reportType: string, filters: Record<string, any>) => {
    setLoading(true)
    try {
      const generated = await reportService.generateReport(datasetId, {
        reportType,
        filters,
      })
      setReport(generated)
      setSearchParams({ reportId: generated.report_id })
      await fetchHistory()
    } catch (err: any) {
      throw err
    } finally {
      setLoading(false)
    }
  }

  // ── Filter reports by search ──
  const filteredReports = reportHistory.filter((r) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      (r.title && r.title.toLowerCase().includes(q)) ||
      (r.domain && r.domain.toLowerCase().includes(q)) ||
      (r.report_id && r.report_id.toLowerCase().includes(q)) ||
      (r.dataset_id && r.dataset_id.toLowerCase().includes(q))
    )
  })

  const currentActiveDataset = datasetList[0]?.id || paramDatasetId || 'default'

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ► DETAIL VIEW — View an individual report
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (activeReportId || report) {
    return (
      <div className="space-y-6 pb-12">
        {/* Navigation Breadcrumb */}
        <PageHeader
          eyebrow="MIS Report Studio"
          title={report ? report.title : 'Executive Report Viewer'}
          description={
            report
              ? `Report ID: ${report.report_id} — Audited from ${report.metadata?.filename || report.dataset_id}`
              : 'Viewing generated executive intelligence report'
          }
          actions={
            <div className="flex items-center gap-2 print:hidden">
              <Button variant="secondary" size="sm" onClick={handleBackToList}>
                <ChevronLeft className="mr-1.5 h-3.5 w-3.5" />
                All Reports
              </Button>
              {report && (
                <>
                  <Link to={`/ai-analyst?datasetId=${report.dataset_id}&reportType=${report.domain}`}>
                    <Button variant="primary" size="sm" className="bg-brand-600 hover:bg-brand-700 text-white font-bold">
                      <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                      Ask AI Analyst
                    </Button>
                  </Link>
                  <Button variant="secondary" size="sm" onClick={handleExportJson}>
                    <Download className="mr-1.5 h-3.5 w-3.5" />
                    JSON
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
                  {generating ? 'Computing Deterministic Analytics...' : 'Loading Executive Report...'}
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  Executing verified analytics via DuckDB & Pandas, calculating domain KPIs, detecting anomalies.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {error && !loading && (
          <ErrorState
            title="Unable to Synthesize Report"
            message={error}
            onRetry={() => void loadOrGenerateReport()}
          />
        )}

        {/* Report Render */}
        {!loading && !error && report && (
          <ErrorBoundary fallbackTitle="Report Section Rendering">
            <UniversalReportRenderer
              report={report}
              onDownloadPdf={handleDownloadPdf}
              isDownloadingPdf={isDownloadingPdf}
              onRegenerate={handleRegenerate}
              isRegenerating={isRegenerating}
              onAiSummary={handleAiSummary}
              isGeneratingAi={isGeneratingAi}
              aiSummaryResult={aiSummaryResult}
              onExportJson={handleExportJson}
              onPrint={() => window.print()}
              onSelectReportType={handleSelectAutonomousModule}
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
        eyebrow="MIS Reporting & Analytics Engine"
        title="Executive MIS Reports"
        description="Deterministic, capability-aware business intelligence reports with ReportLab PDF export and grounded AI summaries."
        actions={
          <div className="flex items-center gap-2.5">
            <Button
              variant="default"
              size="sm"
              onClick={() => setIsModalOpen(true)}
              className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25"
            >
              <Sparkles className="mr-1.5 h-4 w-4" />
              Generate MIS Report
            </Button>
            <Link to="/upload?intent=report_generation">
              <Button variant="outline" size="sm" className="font-semibold text-xs">
                <Plus className="mr-1.5 h-4 w-4" />
                Upload Dataset
              </Button>
            </Link>
          </div>
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
                Deterministic MIS Reporting
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Report Intelligence Library
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Every report belongs strictly to an audited dataset and version. Reproducible, exportable to corporate PDF, and grounded.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 w-full sm:w-auto">
            <div className="rounded-xl bg-white/5 backdrop-blur-sm p-3 min-w-[100px]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-brand-300">Total Reports</p>
              <p className="text-2xl font-black text-white mt-0.5">{reportHistory.length}</p>
            </div>
            <div className="rounded-xl bg-white/5 backdrop-blur-sm p-3 min-w-[100px]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-300">Datasets</p>
              <p className="text-2xl font-black text-emerald-400 mt-0.5">
                {new Set(reportHistory.map((r) => r.dataset_id)).size}
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
            placeholder="Search reports by title, domain, or dataset ID..."
            className="w-full rounded-2xl border border-slate-200 bg-white pl-11 pr-4 py-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <CardSkeleton key={i} lines={3} />
          ))}
        </div>
      )}

      {/* Report Cards Grid */}
      {!loading && filteredReports.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredReports.map((r) => {
            const style = getDomainStyle(r.domain)
            const Icon = style.icon
            const isStale = r.is_stale || r.status === 'stale'

            return (
              <div
                key={r.report_id}
                onClick={() => handleSelectReport(r.report_id)}
                className="group relative text-left overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:border-brand-300 hover:-translate-y-0.5 cursor-pointer"
              >
                {/* Decorative gradient corner */}
                <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-brand-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100 blur-2xl" />

                <div className="relative z-10 space-y-4">
                  {/* Domain badge + Version & Stale tag */}
                  <div className="flex items-center justify-between">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${style.bg} ${style.color} transition-transform duration-200 group-hover:scale-105`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-mono font-bold text-slate-600">
                        v{r.dataset_version || 1}
                      </span>
                      {isStale && (
                        <span className="rounded-md bg-amber-50 border border-amber-200 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                          Stale
                        </span>
                      )}
                      <span className={`rounded-full border ${style.border} ${style.bg} px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${style.color}`}>
                        {(r.domain || 'general').toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {/* Title & Dataset ID */}
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 line-clamp-2 group-hover:text-brand-700 transition-colors">
                      {r.title || 'Untitled Report'}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono truncate">
                      Dataset: {r.dataset_id}
                    </p>
                  </div>

                  {/* Metadata row */}
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

                  {/* Card Actions Footer */}
                  <div className="border-t border-slate-100 pt-3 flex items-center justify-between">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        void reportService.downloadPdf(r.report_id, `${r.title || 'report'}.pdf`)
                      }}
                      className="flex items-center gap-1 text-[11px] font-semibold text-brand-600 hover:text-brand-800 transition"
                    >
                      <Download className="h-3.5 w-3.5" /> PDF
                    </button>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={(e) => handleDeleteReport(e, r.report_id)}
                        className="rounded-lg p-1 text-slate-400 hover:bg-red-50 hover:text-red-600 transition"
                        title="Delete report"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                      <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-slate-50 text-slate-400 group-hover:bg-brand-50 group-hover:text-brand-600 transition">
                        <ChevronLeft className="h-3.5 w-3.5 rotate-180" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Empty Search State */}
      {!loading && reportHistory.length > 0 && filteredReports.length === 0 && (
        <EmptyState
          icon={Search}
          title="No Matching Reports Found"
          description={`No reports matched "${searchQuery}". Check your spelling or clear your filter.`}
          actionLabel="Clear Search"
          onAction={() => setSearchQuery('')}
        />
      )}

      {/* Empty State */}
      {!loading && reportHistory.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No Executive Reports Yet"
          description="Generate professional MIS reports for your business datasets. Capability-aware, deterministic, reproducible, and exportable to ReportLab PDF."
          actionLabel="Generate MIS Report"
          onAction={() => setIsModalOpen(true)}
        />
      )}

      {/* Report Generation Modal */}
      <ReportGenerateModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        currentDatasetId={currentActiveDataset}
        datasetList={datasetList}
        onGenerate={handleGenerateFromModal}
      />
    </div>
  )
}
