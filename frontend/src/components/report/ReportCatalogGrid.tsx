import { useState } from 'react'
import {
  ArrowRight,
  BarChart3,
  ChevronDown,
  ChevronUp,
  Clock,
  Lock,
  PieChart,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react'
import type { ReportTypeStatus } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent, CardHeader } from '../ui/Card'

interface ReportCatalogGridProps {
  reportTypes: ReportTypeStatus[]
  onSelectReportType?: (reportKey: string) => void
  currentReportType?: string
  datasetName?: string
}

export function ReportCatalogGrid({
  reportTypes,
  onSelectReportType,
  currentReportType,
  datasetName,
}: ReportCatalogGridProps) {
  const [showUnavailable, setShowUnavailable] = useState(false)

  if (!reportTypes || reportTypes.length === 0) return null

  const availableModules = reportTypes.filter((rt) => rt.available)
  const unavailableModules = reportTypes.filter((rt) => !rt.available)

  const getIcon = (key: string) => {
    if (key.includes('employee') || key.includes('workforce') || key.includes('gender')) {
      return <Users className="h-5 w-5 text-indigo-600" />
    }
    if (key.includes('attrition') || key.includes('breakdown')) {
      return <PieChart className="h-5 w-5 text-rose-600" />
    }
    if (key.includes('revenue') || key.includes('profit') || key.includes('sales')) {
      return <TrendingUp className="h-5 w-5 text-emerald-600" />
    }
    if (key.includes('experience') || key.includes('joining') || key.includes('year')) {
      return <Clock className="h-5 w-5 text-amber-600" />
    }
    if (key.includes('quality') || key.includes('audit')) {
      return <ShieldCheck className="h-5 w-5 text-teal-600" />
    }
    return <BarChart3 className="h-5 w-5 text-indigo-600" />
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-200/80 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <h2 className="text-base font-bold tracking-tight text-slate-900">
              AI-Generated Report Intelligence
            </h2>
            <Badge variant="brand" className="text-[10px] font-semibold">
              {availableModules.length} Analyses Identified
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            AI evaluated {datasetName ? <span className="font-semibold text-slate-700">{datasetName}</span> : 'the uploaded dataset'} and identified the most relevant business analyses.
          </p>
        </div>
      </div>

      {/* Available Modules Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {availableModules.map((rt) => {
          const isActive = currentReportType === rt.key
          const isHighPriority = rt.priority === 'high'

          return (
            <Card
              key={rt.key}
              className={`transition-all duration-200 flex flex-col justify-between ${
                isActive
                  ? 'border-indigo-500 ring-2 ring-indigo-500/20 shadow-md bg-white'
                  : 'border-slate-200 hover:border-indigo-300 hover:shadow-sm bg-white'
              }`}
            >
              <div>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-50 border border-slate-100 shadow-2xs">
                      {getIcon(rt.key)}
                    </div>
                    <div className="flex items-center gap-1.5">
                      {isActive && (
                        <Badge variant="brand" className="text-[10px]">
                          Active Report
                        </Badge>
                      )}
                      {isHighPriority ? (
                        <Badge variant="success" className="text-[10px] font-medium">
                          AI Recommended
                        </Badge>
                      ) : (
                        <Badge variant="default" className="text-[10px] text-slate-600">
                          {rt.priority === 'medium' ? 'High relevance' : 'Relevant'}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{rt.title}</h3>
                    <p className="text-xs text-slate-500 leading-relaxed mt-1">
                      {rt.description}
                    </p>
                  </div>

                  {/* Live Preview Metrics Pills */}
                  {rt.preview_metrics && rt.preview_metrics.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {rt.preview_metrics.map((metric, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center rounded-md bg-indigo-50/80 px-2 py-0.5 text-[11px] font-semibold text-indigo-700 border border-indigo-100"
                        >
                          {metric}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Why this matters callout */}
                  {(rt.dynamic_insight || rt.relevance_reason) && (
                    <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100 text-[11px] text-slate-600 leading-normal">
                      <span className="font-semibold text-slate-800">Why this matters: </span>
                      {rt.dynamic_insight || rt.relevance_reason}
                    </div>
                  )}
                </CardContent>
              </div>

              {/* Action Button */}
              <div className="px-6 pb-4 pt-2">
                {onSelectReportType && (
                  <Button
                    variant={isActive ? 'primary' : 'outline'}
                    size="sm"
                    className="w-full text-xs font-semibold justify-between group"
                    onClick={() => onSelectReportType(rt.key)}
                  >
                    <span>{isActive ? 'Currently Viewing' : 'Open Analysis'}</span>
                    <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </Button>
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {/* Collapsible Other / Unavailable Analyses */}
      {unavailableModules.length > 0 && (
        <div className="pt-2">
          <button
            type="button"
            className="flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors py-2"
            onClick={() => setShowUnavailable(!showUnavailable)}
          >
            <Lock className="h-3.5 w-3.5 text-slate-400" />
            <span>
              {showUnavailable ? 'Hide' : 'Show'} other analyses requiring additional dataset schema attributes ({unavailableModules.length})
            </span>
            {showUnavailable ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>

          {showUnavailable && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 pt-3">
              {unavailableModules.map((rt) => (
                <Card
                  key={rt.key}
                  className="border-slate-200/60 bg-slate-50/40 opacity-75 text-xs p-4 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700">{rt.title}</span>
                    <Badge variant="default" className="text-[10px]">
                      Unavailable
                    </Badge>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-snug">{rt.description}</p>
                  {rt.missing_capabilities && rt.missing_capabilities.length > 0 && (
                    <div className="text-[10px] text-slate-400 pt-1">
                      <span className="font-medium">Missing: </span>
                      {rt.missing_capabilities.map((c) => c.replace(/_/g, ' ')).join(', ')}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
