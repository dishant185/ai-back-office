import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import type { ReportMetric } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Card, CardContent } from '../ui/Card'

interface MetricCardGridProps {
  metrics: ReportMetric[]
}

export function MetricCardGrid({ metrics }: MetricCardGridProps) {
  if (!metrics || metrics.length === 0) return null

  // Sort by priority ascending
  const sorted = [...metrics].sort((a, b) => (a.priority || 99) - (b.priority || 99))

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {sorted.map((metric) => {
        const hasValue = metric.value !== null && metric.value !== undefined && metric.available !== false
        const isWarning = metric.status === 'warning'
        const isPositive = metric.status === 'positive'

        return (
          <Card
            key={metric.id}
            className="group relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
          >
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-slate-500 line-clamp-1">
                  {metric.name}
                </span>
                {metric.change_pct !== undefined && metric.change_pct !== null && (
                  <span
                    className={`flex items-center text-xs font-semibold ${
                      metric.change_pct > 0
                        ? 'text-emerald-600'
                        : metric.change_pct < 0
                          ? 'text-red-600'
                          : 'text-slate-400'
                    }`}
                  >
                    {metric.change_pct > 0 ? (
                      <ArrowUpRight className="h-3 w-3 mr-0.5" />
                    ) : metric.change_pct < 0 ? (
                      <ArrowDownRight className="h-3 w-3 mr-0.5" />
                    ) : (
                      <Minus className="h-3 w-3 mr-0.5" />
                    )}
                    {Math.abs(metric.change_pct)}%
                  </span>
                )}
                {metric.status && !metric.change_pct && (
                  <span
                    className={`h-2 w-2 rounded-full ${
                      isWarning ? 'bg-amber-500' : isPositive ? 'bg-emerald-500' : 'bg-slate-300'
                    }`}
                  />
                )}
              </div>

              <div className="mt-2.5">
                {hasValue ? (
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-2xl font-bold tracking-tight text-slate-900">
                      {metric.formatted_value || String(metric.value)}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 py-1">
                    <span className="text-xl font-medium text-slate-400">—</span>
                    <Badge variant="default" className="text-[10px] py-0 px-1.5">
                      N/A
                    </Badge>
                  </div>
                )}
              </div>

              {metric.description && (
                <p className="mt-1 text-xs text-slate-400 line-clamp-1">
                  {metric.description}
                </p>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
