import { useState, useMemo } from 'react'
import {
  ArrowRight,
  FileText,
  Lightbulb,
  ShieldAlert,
  X,
} from 'lucide-react'
import type { ReportResponse, DynamicSummarySectionData } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { DataQualityCard } from './DataQualityCard'
import { DynamicExecutiveSummary } from './DynamicExecutiveSummary'
import { ExecutiveSummaryCard } from './ExecutiveSummaryCard'
import { MetricCardGrid } from './MetricCardGrid'
import { ReportCatalogGrid } from './ReportCatalogGrid'
import { ReportHeader } from './ReportHeader'
import { ReportSectionView } from './ReportSectionView'

interface UniversalReportRendererProps {
  report: ReportResponse
  onDownloadPdf?: () => void
  isDownloadingPdf?: boolean
  onRegenerate?: () => void
  isRegenerating?: boolean
  onAiSummary?: () => void
  isGeneratingAi?: boolean
  aiSummaryResult?: Record<string, any> | null
  onExportJson?: () => void
  onPrint?: () => void
  onSelectReportType?: (reportKey: string) => void
}

export function UniversalReportRenderer({
  report,
  onDownloadPdf,
  isDownloadingPdf,
  onRegenerate,
  isRegenerating,
  onAiSummary,
  isGeneratingAi,
  aiSummaryResult,
  onExportJson,
  onPrint,
  onSelectReportType,
}: UniversalReportRendererProps) {
  const [showEvidence, setShowEvidence] = useState(false)

  const summaryPayload = aiSummaryResult?.summary || aiSummaryResult || {}
  const validationPayload = aiSummaryResult?.validation || {}
  const summaryStatus = aiSummaryResult?.status || 'VERIFIED_ANALYTICS_ONLY'
  const isAiGrounded = summaryStatus === 'AI_GENERATED_GROUNDED' && (validationPayload.grounded !== false)

  const summaryTitle = summaryPayload.report_title || summaryPayload.title || `${report.title} Executive Summary`
  const summaryOverview = summaryPayload.overview || summaryPayload.executive_summary || 'Executive summary generated.'
  const summaryFindings = summaryPayload.key_findings || summaryPayload.key_highlights || []
  const summaryPatterns = summaryPayload.important_patterns || []
  const summaryImplications = summaryPayload.business_implications || []
  const summaryRecommendations = summaryPayload.recommendations || []
  const summaryLimitations = summaryPayload.limitations || []

  // Dynamic sections per Phase 6.8 (Rule #27 & #28)
  const dynamicSections: DynamicSummarySectionData[] = useMemo(() => {
    if (summaryPayload.sections && Array.isArray(summaryPayload.sections) && summaryPayload.sections.length > 0) {
      return summaryPayload.sections
    }
    // Fallback adapter for older summaries without explicit sections array
    const fallbackSections: DynamicSummarySectionData[] = []
    if (summaryOverview && summaryOverview !== 'Executive summary generated.') {
      fallbackSections.push({
        type: 'finding',
        title: 'Executive Summary',
        content: summaryOverview,
      })
    }
    summaryFindings.forEach((finding: string) => {
      fallbackSections.push({
        type: 'finding',
        title: 'Key Finding',
        content: finding,
      })
    })
    summaryPatterns.forEach((pat: string) => {
      fallbackSections.push({
        type: 'distribution',
        title: 'Observed Pattern',
        content: pat,
      })
    })
    summaryImplications.forEach((imp: string) => {
      fallbackSections.push({
        type: 'business_implication',
        title: 'Business Implication',
        content: imp,
      })
    })
    summaryRecommendations.forEach((rec: string) => {
      fallbackSections.push({
        type: 'recommendation',
        title: 'Suggested Action',
        content: rec,
      })
    })
    summaryLimitations.forEach((lim: string) => {
      fallbackSections.push({
        type: 'limitation',
        title: 'Data Limitation',
        content: lim,
      })
    })
    return fallbackSections
  }, [summaryPayload, summaryOverview, summaryFindings, summaryPatterns, summaryImplications, summaryRecommendations, summaryLimitations])

  return (
    <div className="space-y-8 animate-fade-in print:space-y-4">
      {/* 1. Header with Metadata & Actions */}
      <ReportHeader
        title={report.title}
        subtitle={report.subtitle}
        domain={report.domain}
        rowCount={report.row_count}
        columnCount={report.column_count}
        generatedAt={report.generated_at}
        datasetVersion={report.dataset_version}
        isStale={report.is_stale || report.status === 'stale'}
        status={report.status}
        onDownloadPdf={onDownloadPdf}
        isDownloadingPdf={isDownloadingPdf}
        onRegenerate={onRegenerate}
        isRegenerating={isRegenerating}
        onAiSummary={onAiSummary}
        isGeneratingAi={isGeneratingAi}
        onExportJson={onExportJson}
        onPrint={onPrint}
      />

      {/* Dynamic AI Executive Summary V2 */}
      {(isGeneratingAi || aiSummaryResult) && (
        <DynamicExecutiveSummary
          summaryData={
            aiSummaryResult
              ? {
                  title: summaryTitle,
                  overview: summaryOverview,
                  sections: dynamicSections,
                  recommendations: summaryRecommendations,
                  limitations: summaryLimitations,
                  status: aiSummaryResult.status || (isAiGrounded ? 'AI_GENERATED_GROUNDED' : 'VERIFIED_ANALYTICS_ONLY'),
                  verified_claims: aiSummaryResult.verified_claims,
                  report_type: aiSummaryResult.report_type || report.report_type,
                  dataset_version: aiSummaryResult.dataset_version || report.dataset_version,
                }
              : null
          }
          isLoading={isGeneratingAi}
          onRegenerate={onAiSummary}
          onViewEvidence={() => setShowEvidence(true)}
          reportTitle={report.title}
          datasetName={typeof report.metadata?.filename === 'string' ? report.metadata.filename : 'dataset.csv'}
          datasetVersion={report.dataset_version}
          reportVersion={1}
        />
      )}

      {/* 2. Standard Executive Summary if AI Summary not explicitly generated */}
      {report.executive_summary && !aiSummaryResult && (
        <ExecutiveSummaryCard summary={report.executive_summary} />
      )}

      {/* 3. Core KPI Stat Grid */}
      {report.kpi_metrics?.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Primary Executive Metrics
            </h2>
            <span className="text-xs text-slate-400">
              {report.kpi_metrics.filter((m) => m.available).length} verified KPIs
            </span>
          </div>
          <MetricCardGrid metrics={report.kpi_metrics} />
        </div>
      )}

      {/* 4. Domain & Analytical Sections */}
      {report.sections?.length > 0 && (
        <div className="space-y-10">
          {report.sections.map((section) => (
            <ReportSectionView key={section.id} section={section} />
          ))}
        </div>
      )}

      {/* 5. Anomalies & Outliers Alert Box */}
      {report.anomalies?.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/40 shadow-sm print:break-inside-avoid">
          <CardHeader className="pb-3 border-b border-amber-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-amber-600" />
                <h3 className="text-xs font-bold text-amber-950 uppercase tracking-wider">
                  Critical Flight Risk & Anomaly Indicators
                </h3>
              </div>
              <Badge variant="warning">{report.anomalies.length} Flagged</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-3">
            <div className="grid gap-3 sm:grid-cols-2">
              {report.anomalies.map((anom) => (
                <div
                  key={anom.id}
                  className="rounded-lg border border-amber-200/80 bg-white/80 p-3 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800">{anom.label}</span>
                    <Badge variant={anom.severity === 'high' ? 'error' : 'warning'}>
                      {anom.value}
                    </Badge>
                  </div>
                  <p className="text-slate-600 leading-snug">{anom.reason}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 6. Strategic Recommendations */}
      {report.recommendations?.length > 0 && (
        <Card className="border-slate-200 shadow-sm print:break-inside-avoid">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-brand-600" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Strategic Recommendations
              </h3>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {report.recommendations.map((rec) => (
              <div
                key={rec.id}
                className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50/50 p-3 transition-colors hover:bg-slate-50"
              >
                <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                  <ArrowRight className="h-3 w-3" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{rec.title}</span>
                    <Badge
                      variant={
                        rec.priority === 'high'
                          ? 'error'
                          : rec.priority === 'medium'
                          ? 'warning'
                          : 'info'
                      }
                    >
                      {rec.priority.toUpperCase()} PRIORITY
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{rec.description}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 7. Comprehensive Data Quality & Health Audit */}
      {report.data_quality && (
        <DataQualityCard quality={report.data_quality} />
      )}

      {/* 8. AI-Generated Report Intelligence Modules */}
      {report.available_report_types?.length > 0 && (
        <div className="print:hidden">
          <ReportCatalogGrid
            reportTypes={report.available_report_types}
            onSelectReportType={onSelectReportType}
            currentReportType={report.report_type}
            datasetName={typeof report.metadata?.filename === 'string' ? report.metadata.filename : undefined}
          />
        </div>
      )}

      {/* View Evidence Modal */}
      {showEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-fade-in">
          <div className="w-full max-w-lg rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden animate-scale-up">
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4 bg-slate-50">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Verified Evidence & Audit Trail</h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 rounded-full text-slate-400 hover:text-slate-600"
                onClick={() => setShowEvidence(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-6 space-y-4 text-xs text-slate-700 max-h-[80vh] overflow-y-auto">
              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Report</span>
                    <span className="font-bold text-slate-900 text-sm">{summaryTitle}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Report Type</span>
                    <span className="font-mono text-slate-800 text-xs">{aiSummaryResult?.report_type || report.report_type}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Dataset</span>
                    <span className="font-medium text-slate-900 text-xs">{typeof report.metadata?.filename === 'string' ? report.metadata.filename : 'dataset.csv'}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Dataset Version</span>
                    <span className="font-mono font-bold text-indigo-700 text-xs">v{aiSummaryResult?.dataset_version || report.dataset_version}</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-2">Verified Deterministic Metrics</div>
                <div className="max-h-48 overflow-y-auto space-y-1.5 border border-slate-200 rounded-lg p-2 bg-white">
                  {report.kpi_metrics?.filter((k) => k.available !== false && k.value !== null).map((k) => (
                    <div key={k.id} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-slate-50 border-b border-slate-100 last:border-0">
                      <span className="text-slate-700 font-medium">{k.name}</span>
                      <span className="font-mono font-bold text-slate-900">{k.formatted_value || String(k.value)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {aiSummaryResult?.verified_claims && aiSummaryResult.verified_claims.length > 0 && (
                <div>
                  <div className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-2">Grounding Verification Claims</div>
                  <div className="max-h-36 overflow-y-auto space-y-1 border border-slate-200 rounded-lg p-2.5 bg-emerald-50/40 text-[11px] text-emerald-900">
                    {aiSummaryResult.verified_claims.map((claim: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-1.5">
                        <span className="text-emerald-600 font-bold">✓</span>
                        <span>{claim}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {summaryLimitations.length > 0 && (
                <div>
                  <div className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-1.5">Evaluated Limitations</div>
                  <ul className="text-[11px] text-slate-600 space-y-1 list-disc pl-4">
                    {summaryLimitations.map((lim: string, idx: number) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="rounded-lg bg-indigo-50 p-2.5 border border-indigo-100 text-[11px] text-indigo-900">
                <span className="font-semibold">Deterministic Authority: </span>
                All numerical metrics are computed strictly by deterministic engines. No calculations are estimated by LLM.
              </div>
            </div>

            <div className="flex justify-end px-6 py-3 border-t border-slate-100 bg-slate-50">
              <Button size="sm" onClick={() => setShowEvidence(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
