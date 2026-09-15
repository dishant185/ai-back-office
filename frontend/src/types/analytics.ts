export interface AnalyticsMetric {
  name: string
  value: number | null
  unit?: string | null
  description?: string
}

export interface AnalyticsTrendPoint {
  date: string
  value: number | null
}

export interface AnalyticsTrend {
  metric: string
  points: AnalyticsTrendPoint[]
  direction: string
}

export interface AnalyticsAnomaly {
  metric: string
  label: string
  value: number | null
  severity: string
  reason: string
}

export interface AnalyticsSummary {
  profile: string
  row_count: number
  column_count: number
  detected_capabilities: Record<string, boolean>
  metric_count: number
}

export interface BreakdownItem {
  label: string
  value: number
  percentage?: number
}

export interface ChartDataPoint {
  label: string
  value: number
}

export interface ReportDefinition {
  key: string
  title: string
  description: string
  profile: string
  required_capabilities: string[]
}

export interface ReportType extends ReportDefinition {
  available: boolean
  status: 'Available' | 'Unavailable'
}

export interface AnalyticsResponse {
  success: boolean
  dataset_id: string
  profile: string
  capabilities: Record<string, boolean>
  summary: AnalyticsSummary | null
  metrics: AnalyticsMetric[]
  trends: AnalyticsTrend[]
  anomalies: AnalyticsAnomaly[]
  notes: string[]
  raw?: Record<string, unknown>
}
