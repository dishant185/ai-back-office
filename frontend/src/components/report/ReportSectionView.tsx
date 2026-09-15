import { Info } from 'lucide-react'
import type { ReportSection } from '../../types/report'
import { ErrorBoundary } from '../ui/ErrorBoundary'
import { DynamicChart } from './DynamicChart'
import { RankingTable } from './RankingTable'

interface ReportSectionViewProps {
  section: ReportSection
}

export function ReportSectionView({ section }: ReportSectionViewProps) {
  if (!section) return null

  return (
    <section className="space-y-4">
      <div className="border-b border-slate-200/80 pb-3">
        <h2 className="text-lg font-bold tracking-tight text-slate-900">{section.title}</h2>
        {section.description && (
          <p className="mt-0.5 text-xs text-slate-500 max-w-3xl leading-relaxed">
            {section.description}
          </p>
        )}
      </div>

      {section.callout && (
        <div className="flex items-start gap-2.5 rounded-xl border border-brand-100 bg-brand-50/50 p-3.5 text-xs text-brand-900">
          <Info className="h-4 w-4 shrink-0 text-brand-600 mt-0.5" />
          <span className="leading-relaxed font-medium">{section.callout}</span>
        </div>
      )}

      {/* Charts Grid */}
      {section.charts?.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {section.charts.map((chart) => (
            <ErrorBoundary key={chart.id} fallbackTitle={`Chart: ${chart.title || 'Visualization'}`}>
              <DynamicChart chart={chart} />
            </ErrorBoundary>
          ))}
        </div>
      )}

      {/* Rankings */}
      {section.rankings?.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {section.rankings.map((ranking) => (
            <ErrorBoundary key={ranking.id} fallbackTitle={`Ranking: ${ranking.title || 'Table'}`}>
              <RankingTable ranking={ranking} />
            </ErrorBoundary>
          ))}
        </div>
      )}
    </section>
  )
}
