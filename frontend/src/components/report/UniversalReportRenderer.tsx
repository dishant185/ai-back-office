import {
  ArrowRight,
  Lightbulb,
  ShieldAlert,
} from 'lucide-react'
import type { ReportResponse } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { DataQualityCard } from './DataQualityCard'
import { ExecutiveSummaryCard } from './ExecutiveSummaryCard'
import { MetricCardGrid } from './MetricCardGrid'
import { ReportCatalogGrid } from './ReportCatalogGrid'
import { ReportHeader } from './ReportHeader'
import { ReportSectionView } from './ReportSectionView'

interface UniversalReportRendererProps {
  report: ReportResponse
  onExportJson?: () => void
  onPrint?: () => void
}

export function UniversalReportRenderer({
  report,
  onExportJson,
  onPrint,
}: UniversalReportRendererProps) {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. Header with Metadata */}
      <ReportHeader
        title={report.title}
        subtitle={report.subtitle}
        domain={report.domain}
        rowCount={report.row_count}
        columnCount={report.column_count}
        generatedAt={report.generated_at}
        onExportJson={onExportJson}
        onPrint={onPrint}
      />

      {/* 2. Executive Summary */}
      {report.executive_summary && (
        <ExecutiveSummaryCard summary={report.executive_summary} />
      )}

      {/* 3. Core KPI Stat Grid */}
      {report.kpi_metrics?.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
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
        <Card className="border-amber-200 bg-amber-50/40 shadow-sm">
          <CardHeader className="pb-3 border-b border-amber-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                  <ShieldAlert className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Outlier & Risk Anomaly Detections
                  </h3>
                  <p className="text-xs text-slate-600">
                    Automated anomaly detection comparing observed distributions against benchmark ranges
                  </p>
                </div>
              </div>
              <Badge variant="warning">{report.anomalies.length} Flagged</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {report.anomalies.map((anom) => (
              <div
                key={anom.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-amber-100 bg-white p-3.5"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">{anom.label}</span>
                    <Badge variant={anom.severity === 'high' ? 'error' : 'warning'}>
                      {(anom.severity || 'warning').toUpperCase()}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-slate-600 leading-relaxed">{anom.reason}</p>
                </div>
                <div className="text-right sm:border-l sm:border-slate-100 sm:pl-4">
                  <div className="text-xs text-slate-400">Observed vs Expected</div>
                  <div className="text-sm font-bold text-slate-900">
                    {anom.value ?? '—'} <span className="text-xs font-normal text-slate-400">({anom.expected ?? 'N/A'})</span>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 6. Strategic Recommendations */}
      {report.recommendations?.length > 0 && (
        <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/20 via-white to-white shadow-sm">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                <Lightbulb className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Strategic & Operational Recommendations
                </h3>
                <p className="text-xs text-slate-500">
                  Data-driven interventions prioritized by operational impact
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {report.recommendations.map((rec) => (
              <div
                key={rec.id}
                className="flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-3.5 transition hover:border-slate-200"
              >
                <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600 font-semibold text-xs">
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
                      {rec.priority} priority
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{rec.description}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 7. Data Quality Audit */}
      {report.data_quality && <DataQualityCard quality={report.data_quality} />}

      {/* 8. Available Report Modules Catalog */}
      {report.available_report_types?.length > 0 && (
        <ReportCatalogGrid reportTypes={report.available_report_types} />
      )}
    </div>
  )
}
