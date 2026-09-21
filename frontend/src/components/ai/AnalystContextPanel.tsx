/**
 * AnalystContextPanel — Right-side panel showing dataset/AI context.
 */
import { BarChart3, Cpu, Database, Layers } from 'lucide-react'
import { Card, CardContent } from '../ui/Card'
import type { AnalystSession } from '../../types/ai'

interface AnalystContextPanelProps {
  session: AnalystSession | null
  aiStatus: string
  aiModel: string
}

const PROFILE_LABELS: Record<string, string> = {
  hr: 'HR / Workforce',
  sales: 'Sales / Revenue',
  finance: 'Finance / Accounting',
  inventory: 'Inventory / Supply Chain',
  customer: 'Customer / CRM',
  marketing: 'Marketing',
  automobile: 'Automobile',
  generic: 'General Analytics',
}

const CAPABILITY_LABELS: Record<string, string> = {
  employee_analysis: 'Employee Analysis',
  attrition_analysis: 'Attrition Analysis',
  age_analysis: 'Age Analysis',
  city_analysis: 'City Analysis',
  education_analysis: 'Education Analysis',
  payment_tier_analysis: 'Compensation Analysis',
  gender_analysis: 'Gender Analysis',
  experience_analysis: 'Experience Analysis',
  bench_analysis: 'Bench Analysis',
  revenue_analysis: 'Revenue Analysis',
  profit_analysis: 'Profit Analysis',
  volume_analysis: 'Volume Analysis',
  product_analysis: 'Product Analysis',
  regional_analysis: 'Regional Analysis',
  time_series_analysis: 'Time Series',
  joining_year_analysis: 'Joining Year',
  target_analysis: 'Target Analysis',
  revenue: 'Revenue',
  profit: 'Profit',
  quantity: 'Quantity',
  time_series: 'Time Series',
}

const METRIC_DISPLAY: Record<string, string> = {
  employee_count: 'Employee Count',
  average_age: 'Avg Age',
  avg_joining_year: 'Avg Joining Year',
  employees_left: 'Employees Left',
  employees_retained: 'Retained',
  attrition_rate: 'Attrition Rate',
  total_revenue: 'Total Revenue',
  total_profit: 'Total Profit',
  total_quantity: 'Total Quantity',
}

export function AnalystContextPanel({ session, aiStatus, aiModel }: AnalystContextPanelProps) {
  if (!session) {
    return (
      <Card className="border-slate-200/80 shadow-sm">
        <CardContent className="p-5">
          <p className="text-xs text-slate-400">Loading context...</p>
        </CardContent>
      </Card>
    )
  }

  const profileLabel = PROFILE_LABELS[session.profile] || session.profile
  const capabilities = session.capabilities || []
  const metrics = session.metrics || {}

  return (
    <div className="space-y-4">
      {/* Dataset Info */}
      <Card className="border-slate-200/80 shadow-sm">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-brand-500" />
            <span className="text-xs font-bold text-slate-900">Dataset</span>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Profile</span>
              <span className="text-[11px] font-semibold text-slate-700">{profileLabel}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Records</span>
              <span className="text-[11px] font-semibold text-slate-700">{session.row_count.toLocaleString()}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Capabilities */}
      {capabilities.length > 0 && (
        <Card className="border-slate-200/80 shadow-sm">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-brand-500" />
              <span className="text-xs font-bold text-slate-900">Capabilities</span>
            </div>
            <div className="space-y-1">
              {capabilities.slice(0, 8).map((cap) => (
                <div key={cap} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  <span className="text-[11px] text-slate-600">{CAPABILITY_LABELS[cap] || cap}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metrics */}
      {Object.keys(metrics).length > 0 && (
        <Card className="border-slate-200/80 shadow-sm">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-brand-500" />
              <span className="text-xs font-bold text-slate-900">Verified Metrics</span>
            </div>
            <div className="space-y-1.5">
              {Object.entries(metrics).slice(0, 8).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-500">{METRIC_DISPLAY[key] || key}</span>
                  <span className="text-[11px] font-semibold text-slate-700 tabular-nums">
                    {typeof value === 'number'
                      ? value % 1 !== 0
                        ? value.toFixed(2)
                        : value.toLocaleString()
                      : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Runtime */}
      <Card className="border-slate-200/80 shadow-sm">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-brand-500" />
            <span className="text-xs font-bold text-slate-900">AI Runtime</span>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Status</span>
              <span className="text-[11px] font-semibold text-slate-700 capitalize">{aiStatus || 'Offline'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Provider</span>
              <span className="text-[11px] font-semibold text-slate-700">Local</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Model</span>
              <span className="text-[11px] font-semibold text-slate-700 truncate max-w-[120px]">{aiModel || 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Runtime</span>
              <span className="text-[11px] font-semibold text-slate-700">llama.cpp</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-500">Compute</span>
              <span className="text-[11px] font-semibold text-slate-700">CPU</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
