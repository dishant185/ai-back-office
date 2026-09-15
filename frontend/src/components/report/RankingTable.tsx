import type { ReportRanking } from '../../types/report'
import { Card, CardContent, CardHeader } from '../ui/Card'

interface RankingTableProps {
  ranking: ReportRanking
}

export function RankingTable({ ranking }: RankingTableProps) {
  if (!ranking || !ranking.items || ranking.items.length === 0) return null

  const maxValue = Math.max(...ranking.items.map((it) => it.value || 0), 1)

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <h3 className="text-sm font-semibold text-slate-900">{ranking.title}</h3>
      </CardHeader>
      <CardContent className="pt-0 space-y-3">
        {ranking.items.map((item) => {
          const barWidth = Math.min(100, Math.max(8, (item.value / maxValue) * 100))

          return (
            <div key={item.rank} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded font-semibold text-[11px] ${
                      item.rank === 1
                        ? 'bg-amber-100 text-amber-800'
                        : item.rank === 2
                          ? 'bg-slate-200 text-slate-700'
                          : item.rank === 3
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {item.rank}
                  </span>
                  <span className="font-medium text-slate-700 truncate max-w-[180px] sm:max-w-[240px]">
                    {item.label}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {item.pct_of_total !== undefined && item.pct_of_total !== null && (
                    <span className="text-slate-400 text-[11px]">{item.pct_of_total}%</span>
                  )}
                  <span className="font-semibold text-slate-900">{item.formatted_value}</span>
                </div>
              </div>

              {/* Visual bar */}
              <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand-500 transition-all duration-500"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
