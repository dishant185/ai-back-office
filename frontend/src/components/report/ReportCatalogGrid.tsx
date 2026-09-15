import {
  BarChart3,
  Check,
  Lock,
  PieChart,
  TrendingUp,
  Users,
} from 'lucide-react'
import type { ReportTypeStatus } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader } from '../ui/Card'

interface ReportCatalogGridProps {
  reportTypes: ReportTypeStatus[]
}

export function ReportCatalogGrid({ reportTypes }: ReportCatalogGridProps) {
  if (!reportTypes || reportTypes.length === 0) return null

  const getIcon = (key: string) => {
    if (key.includes('employee') || key.includes('workforce') || key.includes('demographics')) {
      return <Users className="h-5 w-5 text-brand-600" />
    }
    if (key.includes('attrition') || key.includes('breakdown')) {
      return <PieChart className="h-5 w-5 text-brand-600" />
    }
    if (key.includes('revenue') || key.includes('profit') || key.includes('sales')) {
      return <TrendingUp className="h-5 w-5 text-brand-600" />
    }
    return <BarChart3 className="h-5 w-5 text-brand-600" />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-slate-900">
            Autonomous Report Modules
          </h2>
          <p className="text-xs text-slate-500">
            Dynamically evaluated capabilities based on standardized dataset schema
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {reportTypes.map((rt) => (
          <Card
            key={rt.key}
            className={`transition-all duration-200 ${
              rt.available
                ? 'border-brand-200/70 hover:border-brand-400 hover:shadow-sm bg-white'
                : 'border-slate-200/60 bg-slate-50/40 opacity-70'
            }`}
          >
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                    rt.available ? 'bg-brand-50' : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  {getIcon(rt.key)}
                </div>
                {rt.available ? (
                  <Badge variant="success">
                    <Check className="mr-1 h-3 w-3" />
                    Available
                  </Badge>
                ) : (
                  <Badge variant="default">
                    <Lock className="mr-1 h-3 w-3" />
                    Unavailable
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <h3 className="text-sm font-bold text-slate-900">{rt.title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
                {rt.description}
              </p>

              {!rt.available && rt.missing_capabilities?.length > 0 && (
                <div className="pt-2 text-[11px] text-slate-400">
                  <span className="font-medium">Missing: </span>
                  {rt.missing_capabilities.map((c) => c.replace(/_/g, ' ')).join(', ')}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
