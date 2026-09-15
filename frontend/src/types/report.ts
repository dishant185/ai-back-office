export interface DataQualityIssue {
  severity: 'info' | 'warning' | 'critical'
  column?: string | null
  description: string
}

export interface DataQuality {
  score: number
  total_rows: number
  total_columns: number
  missing_cells: number
  missing_pct: number
  duplicate_rows: number
  duplicate_pct: number
  completeness_pct: number
  issues: DataQualityIssue[]
}

export interface ReportMetric {
  id: string
  name: string
  value: number | string | null
  formatted_value: string
  unit?: string | null
  description?: string | null
  change_pct?: number | null
  priority: number
  category: string
  status?: 'positive' | 'negative' | 'neutral' | 'warning' | null
  available: boolean
  unavailability_reason?: string | null
}

export interface ChartDataPoint {
  label: string
  value: number | null
  secondary_value?: number | null
  percentage?: number
  category?: string | null
}

export interface ChartDefinition {
  id: string
  title: string
  chart_type: 'bar' | 'line' | 'donut' | 'histogram' | 'horizontal_bar' | 'area'
  description?: string | null
  data: ChartDataPoint[]
  x_key: string
  y_key: string
  secondary_y_key?: string | null
  unit?: string | null
}

export interface RankingItem {
  rank: number
  label: string
  value: number
  formatted_value: string
  pct_of_total?: number | null
  subtext?: string | null
}

export interface ReportRanking {
  id: string
  title: string
  dimension: string
  metric: string
  items: RankingItem[]
}

export interface ReportAnomaly {
  id: string
  metric: string
  label: string
  value: string | number | null
  expected?: string | number | null
  severity: 'low' | 'medium' | 'high'
  reason: string
}

export interface ReportRecommendation {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  category: 'retention' | 'optimization' | 'operational' | 'financial' | string
}

export interface ReportSection {
  id: string
  title: string
  description?: string | null
  metrics: ReportMetric[]
  charts: ChartDefinition[]
  rankings: ReportRanking[]
  callout?: string | null
}

export interface ExecutiveSummary {
  overview: string
  key_highlights: string[]
  critical_findings: string[]
  sentiment: 'positive' | 'neutral' | 'cautionary'
}

export interface ReportTypeStatus {
  key: string
  title: string
  description: string
  domain: string
  available: boolean
  status: 'Available' | 'Unavailable'
  required_capabilities: string[]
  missing_capabilities: string[]
}

export interface ReportResponse {
  report_id: string
  dataset_id: string
  title: string
  subtitle: string
  domain: string
  generated_at: string
  row_count: number
  column_count: number
  executive_summary: ExecutiveSummary
  kpi_metrics: ReportMetric[]
  sections: ReportSection[]
  anomalies: ReportAnomaly[]
  data_quality: DataQuality
  recommendations: ReportRecommendation[]
  available_report_types: ReportTypeStatus[]
  metadata: Record<string, unknown>
}

export interface ReportSummaryItem {
  report_id: string
  dataset_id: string
  title: string
  domain: string
  generated_at: string
  row_count: number
}
