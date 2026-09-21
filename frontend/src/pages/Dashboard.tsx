import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  Clock,
  Cpu,
  Database,
  FileSpreadsheet,
  FileText,
  Layers,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Upload,
  Zap,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { StatCardSkeleton, TableSkeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { reportService } from '../services/reportService'
import api from '../services/api'
import type { ReportSummaryItem } from '../types/report'

interface DashboardUpload {
  upload_id: string
  filename: string
  file_type: string
  file_size: number
  rows: number
  columns: number
  missing_cells: number
  completeness: number
  created_at: string
}

interface DashboardStats {
  total_uploads: number
  total_reports: number
  total_mappings: number
  total_records: number
  recent_uploads: DashboardUpload[]
  recent_activity: Array<{
    type: string
    title: string
    description: string
    timestamp: string
    badge: string
  }>
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** index
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`
}

function timeAgo(isoString: string | null | undefined): string {
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

export default function Dashboard() {
  const navigate = useNavigate()

  const {
    data: reports = [],
    isLoading: loadingReports,
    isError: isReportsError,
    error: reportsError,
    refetch: refetchReports,
  } = useQuery<ReportSummaryItem[]>({
    queryKey: ['dashboard-reports'],
    queryFn: () => reportService.listReports(),
  })

  const {
    data: stats,
    isLoading: loadingStats,
    isError: isStatsError,
    error: statsError,
    refetch: refetchStats,
  } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStats>('/api/v1/dashboard/stats')
      return response.data
    },
  })

  const totalRecords = stats?.total_records || reports.reduce((acc, r) => acc + (r.row_count || 0), 0)

  return (
    <ErrorBoundary fallbackTitle="Dashboard Error">
      <div className="space-y-8 animate-fade-in pb-12">
      {/* Executive Command Center Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-10 text-white shadow-xl shadow-slate-900/10">
        <div className="pointer-events-none absolute -right-16 -top-16 h-72 w-72 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-72 w-72 rounded-full bg-purple-500/15 blur-3xl" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div className="space-y-4 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="flex items-center gap-1.5 rounded-full border border-brand-400/30 bg-brand-500/20 px-3 py-1 text-xs font-bold uppercase tracking-wider text-brand-300">
                <Sparkles className="h-3.5 w-3.5 text-brand-400" />
                Executive Copilot Command
              </span>
              <span className="flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Autonomous Engine Active
              </span>
            </div>

            <h1 className="text-2xl sm:text-4xl font-black tracking-tight text-white leading-tight">
              Operational Intelligence &amp; Autonomous Back-Office
            </h1>

            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              Synthesize executive-grade analytics from raw spreadsheets in seconds. Zero hallucinations,
              deterministic statistical computation, and automated canonical schema harmonization.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link to="/upload">
                <Button variant="default" size="md" className="bg-brand-500 hover:bg-brand-600 text-white font-bold shadow-lg shadow-brand-500/30 border-0">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Dataset
                </Button>
              </Link>
              <Link to="/reports">
                <Button variant="outline" size="md" className="border-white/20 bg-white/10 text-white hover:bg-white/20 backdrop-blur-sm">
                  <FileText className="mr-2 h-4 w-4" />
                  View Intelligence Reports
                </Button>
              </Link>
              <Link to="/ai-analyst">
                <Button variant="ghost" size="md" className="text-slate-300 hover:bg-white/10 hover:text-white">
                  <Sparkles className="mr-1.5 h-4 w-4 text-brand-400" />
                  Ask AI Analyst
                </Button>
              </Link>
            </div>
          </div>

          {/* Quick live telemetry pill */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md min-w-[220px]">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Deterministic Mode</span>
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
              </div>
              <p className="text-xl font-extrabold text-white mt-1">100% Math Audit</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Pandas &amp; Python Native</p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md min-w-[220px]">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Active Pipeline</span>
                <Cpu className="h-4 w-4 text-brand-400" />
              </div>
              <p className="text-xl font-extrabold text-white mt-1">{stats?.total_reports ?? reports.length} Reports Ready</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Automated Profiling</p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metric Tiles */}
      {loadingStats ? (
        <StatCardSkeleton count={4} />
      ) : isStatsError ? (
        <ErrorState
          title="Unable to load operational metrics"
          message={(statsError as Error)?.message || 'Failed to fetch platform metrics.'}
          onRetry={() => refetchStats()}
        />
      ) : (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          {/* Metric 1 */}
          <Card className="relative overflow-hidden border-border bg-surface-raised shadow-2xs transition hover:shadow-xs hover:border-brand-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/10 rounded-full blur-2xl -mr-6 -mt-6 pointer-events-none" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">Processed Records</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400">
                  <Database className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl sm:text-3xl font-black text-text-primary tracking-tight">
                {totalRecords > 0 ? totalRecords.toLocaleString() : '0'}
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                <TrendingUp className="h-3.5 w-3.5" />
                <span>100% Deterministic Integrity</span>
              </div>
            </CardContent>
          </Card>

          {/* Metric 2 */}
          <Card className="relative overflow-hidden border-border bg-surface-raised shadow-2xs transition hover:shadow-xs hover:border-violet-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-violet-500/10 rounded-full blur-2xl -mr-6 -mt-6 pointer-events-none" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">Executive Reports</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 dark:bg-violet-950/60 text-violet-600 dark:text-violet-400">
                  <FileSpreadsheet className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl sm:text-3xl font-black text-text-primary tracking-tight">
                {stats?.total_reports ?? reports.length}
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-xs text-brand-600 dark:text-brand-400 font-semibold">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Multi-domain C-Suite Briefs</span>
              </div>
            </CardContent>
          </Card>

          {/* Metric 3 */}
          <Card className="relative overflow-hidden border-border bg-surface-raised shadow-2xs transition hover:shadow-xs hover:border-emerald-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl -mr-6 -mt-6 pointer-events-none" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">Datasets Uploaded</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
                  <Layers className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl sm:text-3xl font-black text-text-primary tracking-tight">
                {stats?.total_uploads ?? 0}
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                <Zap className="h-3.5 w-3.5" />
                <span>Ingested &amp; Profiled</span>
              </div>
            </CardContent>
          </Card>

          {/* Metric 4 */}
          <Card className="relative overflow-hidden border-border bg-surface-raised shadow-2xs transition hover:shadow-xs hover:border-indigo-300">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl -mr-6 -mt-6 pointer-events-none" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-text-muted">Schema Mappings</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                  <Sparkles className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-3 text-2xl sm:text-3xl font-black text-text-primary tracking-tight">
                {stats?.total_mappings ?? 0}
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 font-semibold">
                <Activity className="h-3.5 w-3.5" />
                <span>Column Harmonizations Applied</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Command Center Grid */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left 2-Column: Reports & Datasets */}
        <div className="lg:col-span-2 space-y-8">
          {/* Section: Recent Executive Reports */}
          <Card className="border-slate-200/80 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Recent Executive Intelligence Reports</h2>
                <p className="text-xs text-slate-500">Deterministic reports generated across talent, revenue, and operations.</p>
              </div>
              <Link to="/reports">
                <Button variant="ghost" size="sm" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
                  View All ({reports.length})
                  <ArrowRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {loadingReports ? (
                <TableSkeleton rows={4} cols={3} />
              ) : isReportsError ? (
                <ErrorState
                  title="Unable to load stored reports"
                  message={(reportsError as Error)?.message || 'Failed to fetch executive reports.'}
                  onRetry={() => refetchReports()}
                />
              ) : reports.length === 0 ? (
                <EmptyState
                  icon={FileSpreadsheet}
                  title="No Intelligence Reports Yet"
                  description="Upload your first CSV or Excel file to generate an autonomous, C-suite grade executive report."
                  actionLabel="Generate First Report"
                  onAction={() => navigate('/upload')}
                />
              ) : (
                <div className="space-y-3">
                  {reports.slice(0, 5).map((rep) => {
                    const domainUpper = (rep.domain || 'GENERIC').toUpperCase()
                    const domainColor =
                      rep.domain === 'hr'
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : rep.domain === 'sales'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : rep.domain === 'finance'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-indigo-50 text-indigo-700 border-indigo-200'

                    return (
                      <div
                        key={rep.report_id}
                        onClick={() => navigate(`/reports?reportId=${rep.report_id}`)}
                        className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white p-4 transition-all duration-200 hover:border-brand-300 hover:bg-brand-50/20 hover:shadow-sm cursor-pointer"
                      >
                        <div className="flex items-start sm:items-center gap-3.5">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700 group-hover:bg-brand-100 group-hover:text-brand-700 transition">
                            <FileSpreadsheet className="h-5 w-5" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-bold text-slate-900 group-hover:text-brand-700 transition">
                                {rep.title}
                              </p>
                              <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${domainColor}`}>
                                {domainUpper}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                              <span>{rep.row_count?.toLocaleString()} rows</span>
                              <span>&bull;</span>
                              <span>ID: {rep.report_id}</span>
                              {rep.generated_at && (
                                <>
                                  <span>&bull;</span>
                                  <span className="flex items-center gap-1">
                                    <Clock className="h-3 w-3" />
                                    {new Date(rep.generated_at).toLocaleDateString()}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-end sm:self-center">
                          <Button variant="secondary" size="sm" className="group-hover:bg-brand-500 group-hover:text-white transition">
                            <span>Open Report</span>
                            <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Section: Ingested Operational Datasets — from API */}
          <Card className="border-slate-200/80 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Ingested Operational Datasets</h2>
                <p className="text-xs text-slate-500">Cleaned and standardized tabular files available for audit.</p>
              </div>
              <Link to="/upload">
                <Button variant="secondary" size="sm">
                  <Upload className="mr-1.5 h-3.5 w-3.5" />
                  Import Dataset
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {loadingStats ? (
                <TableSkeleton rows={3} cols={2} />
              ) : isStatsError ? (
                <ErrorState
                  title="Unable to load datasets"
                  message={(statsError as Error)?.message || 'Failed to fetch uploaded datasets.'}
                  onRetry={() => refetchStats()}
                />
              ) : !stats?.recent_uploads?.length ? (
                <EmptyState
                  icon={Database}
                  title="No Datasets Uploaded Yet"
                  description="Upload your first CSV or Excel file to start profiling and standardizing your data."
                  actionLabel="Upload First Dataset"
                  onAction={() => navigate('/upload')}
                />
              ) : (
                <div className="divide-y divide-slate-100">
                  {stats.recent_uploads.slice(0, 5).map((ds) => (
                    <div key={ds.upload_id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-3.5 first:pt-0 last:pb-0">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                          <Database className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-800">{ds.filename}</p>
                          <p className="text-xs text-slate-400">
                            {ds.rows?.toLocaleString() || 0} rows &bull; {ds.columns || 0} columns &bull; {formatBytes(ds.file_size)} &bull; {timeAgo(ds.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 self-end sm:self-center">
                        <div className="text-right">
                          <p className="text-xs font-bold text-slate-700">
                            {ds.completeness ? `${Number(ds.completeness).toFixed(1)}%` : '—'} Quality
                          </p>
                          <p className="text-[10px] text-emerald-600 font-semibold">Audited &amp; Ready</p>
                        </div>
                        <Link to={`/mapping/${ds.upload_id}`}>
                          <Button variant="ghost" size="sm" className="text-slate-500 hover:text-brand-600">
                            Map Schema
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                  {stats.recent_uploads.length > 5 && (
                    <div className="pt-3 text-center">
                      <Link to="/upload">
                        <Button variant="ghost" size="sm" className="text-xs text-brand-600 hover:text-brand-700 font-semibold">
                          View All {stats.recent_uploads.length} Datasets
                          <ArrowRight className="ml-1 h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right 1-Column: Copilot Insights & Quick Hub */}
        <div className="space-y-8">
          {/* Quick Hub Studio */}
          <Card className="border-slate-200/80 shadow-sm">
            <CardHeader className="pb-3">
              <h2 className="text-base font-bold text-slate-900">Autonomous Copilot Studio</h2>
              <p className="text-xs text-slate-500">Instant shortcuts for your analytical workflow.</p>
            </CardHeader>
            <CardContent className="space-y-2.5">
              {[
                {
                  title: 'Upload & Profile Dataset',
                  desc: 'Import CSV / XLSX with instant null audit',
                  icon: Upload,
                  href: '/upload',
                  color: 'bg-brand-50 text-brand-600',
                },
                {
                  title: 'Column Mapping Studio',
                  desc: 'Harmonize source columns with canonical schema',
                  icon: Layers,
                  href: '/mapping',
                  color: 'bg-indigo-50 text-indigo-600',
                },
                {
                  title: 'Universal Report Engine',
                  desc: 'Deterministic executive charts & recommendations',
                  icon: FileText,
                  href: '/reports',
                  color: 'bg-violet-50 text-violet-600',
                },
                {
                  title: 'Conversational AI Analyst',
                  desc: 'Ask questions in plain English with code answers',
                  icon: Sparkles,
                  href: '/ai-analyst',
                  color: 'bg-emerald-50 text-emerald-600',
                },
              ].map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.title}
                    to={item.href}
                    className="group flex items-center gap-3.5 rounded-2xl border border-slate-100 bg-white p-3.5 transition-all duration-200 hover:border-brand-300 hover:bg-brand-50/30 hover:shadow-sm"
                  >
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${item.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-slate-900 group-hover:text-brand-700 transition">
                        {item.title}
                      </p>
                      <p className="text-[11px] text-slate-500 truncate mt-0.5">{item.desc}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-500" />
                  </Link>
                )
              })}
            </CardContent>
          </Card>

          {/* AI Business Analyst Card */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-600 via-indigo-600 to-violet-600 p-5 shadow-lg shadow-brand-500/20">
            <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
            <div className="pointer-events-none absolute -left-6 -bottom-6 h-24 w-24 rounded-full bg-violet-400/20 blur-2xl" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/15 backdrop-blur-sm">
                  <Sparkles className="h-3.5 w-3.5 text-white" />
                </div>
                <span className="text-[11px] font-bold text-white/80 uppercase tracking-wider">AI Business Analyst</span>
              </div>
              <p className="text-base font-extrabold text-white leading-snug">
                Ask questions. Discover insights. Make better decisions.
              </p>
              <p className="text-xs text-white/60 mt-1.5 leading-relaxed">
                Powered by verified deterministic analytics + local AI.
              </p>
              <Link to="/ai-analyst" className="mt-4 block">
                <button className="w-full flex items-center justify-center gap-2 rounded-xl bg-white/15 backdrop-blur-sm border border-white/20 px-4 py-2.5 text-sm font-bold text-white transition-all duration-200 hover:bg-white/25 hover:border-white/30 hover:shadow-lg active:scale-[0.98]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Ask AI Analyst
                </button>
              </Link>
            </div>
          </div>

          {/* Autonomous Copilot Recommendations — dynamic from recent activity */}
          <Card className="border-slate-200/80 shadow-sm bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white">
            <CardHeader className="pb-3 border-b border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-brand-400" />
                  <h3 className="text-sm font-bold text-white">Recent Activity</h3>
                </div>
                <Badge variant="brand" className="bg-brand-500/20 text-brand-300 border-brand-400/30 text-[10px]">
                  Live
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-4 text-xs">
              {loadingStats ? (
                <div className="py-6 text-center">
                  <RefreshCw className="mx-auto h-5 w-5 animate-spin text-brand-400 mb-2" />
                  <p className="text-slate-400 text-xs">Loading activity...</p>
                </div>
              ) : stats?.recent_activity && stats.recent_activity.length > 0 ? (
                stats.recent_activity.slice(0, 3).map((item, idx) => {
                  const iconColor =
                    item.type === 'upload' ? 'text-emerald-400' :
                    item.type === 'report' ? 'text-brand-300' :
                    'text-violet-300'
                  const IconComp =
                    item.type === 'upload' ? Database :
                    item.type === 'report' ? FileText :
                    Layers

                  return (
                    <div key={idx} className="rounded-xl border border-white/10 bg-white/5 p-3.5 backdrop-blur-sm">
                      <p className={`font-bold ${iconColor} flex items-center gap-1.5`}>
                        <IconComp className="h-3.5 w-3.5" />
                        {item.title}
                      </p>
                      <p className="text-slate-300 mt-1 leading-relaxed">
                        {item.description}
                      </p>
                      <p className="text-slate-500 mt-1 text-[10px]">{timeAgo(item.timestamp)}</p>
                    </div>
                  )
                })
              ) : (
                <div className="rounded-xl border border-white/10 bg-white/5 p-3.5 backdrop-blur-sm">
                  <p className="font-bold text-slate-400 flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5" />
                    No activity yet
                  </p>
                  <p className="text-slate-500 mt-1 leading-relaxed">
                    Upload a dataset to see your activity trail here.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      </div>
    </ErrorBoundary>
  )
}
