import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ChartDefinition } from '../../types/report'
import { Card, CardContent, CardHeader } from '../ui/Card'
import {
  CHART_PALETTE,
  CHART_TOOLTIP_STYLE,
  CHART_GRID_STYLE,
  CHART_AXIS_STYLE,
  getChartColor,
} from '../../lib/chartTheme'

interface DynamicChartProps {
  chart: ChartDefinition
}

export function DynamicChart({ chart }: DynamicChartProps) {
  if (!chart || !chart.data || chart.data.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2 border-b border-novera-rule dark:border-white/10">
          <h3 className="text-xs font-semibold text-novera-ink dark:text-novera-dark-ink font-sans">
            {chart?.title || 'Visual Ledger'}
          </h3>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center text-xs font-mono text-novera-muted">
          No verified data points available for this visualization
        </CardContent>
      </Card>
    )
  }

  const { chart_type, title, description, data, x_key, y_key, unit } = chart

  const formatTooltipValue = (val: any) => {
    if (val === null || val === undefined) return '—'
    if (unit === 'percent') return `${val}%`
    if (unit === 'currency') return `$${Number(val).toLocaleString()}`
    if (typeof val === 'number') return val.toLocaleString()
    return String(val)
  }

  const primaryColor = CHART_PALETTE[0]

  return (
    <Card className="rounded-[2px] border border-novera-rule dark:border-white/10 bg-novera-sheet dark:bg-novera-dark-sheet shadow-2xs">
      <CardHeader className="pb-2 border-b border-novera-rule/50 dark:border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-[1px] bg-novera-green" />
              <h3 className="text-xs font-semibold text-novera-ink dark:text-novera-dark-ink font-sans">
                {title}
              </h3>
            </div>
            {description && (
              <p className="text-[11px] text-novera-secondary dark:text-novera-dark-secondary mt-0.5 pl-3.5">
                {description}
              </p>
            )}
          </div>
          {unit && (
            <span className="font-mono text-[10px] text-novera-muted px-1.5 py-0.5 rounded-[1px] bg-novera-sunken dark:bg-white/5 border border-novera-rule/40 dark:border-white/10">
              {unit}
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {chart_type === 'donut' ? (
              <PieChart>
                <Tooltip
                  formatter={(value: any, name: any) => [formatTooltipValue(value), name]}
                  {...CHART_TOOLTIP_STYLE}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="square"
                  formatter={(value) => (
                    <span className="text-[11px] font-mono text-novera-secondary dark:text-novera-dark-secondary">
                      {value}
                    </span>
                  )}
                />
                <Pie
                  data={data}
                  dataKey={y_key}
                  nameKey={x_key}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={2}
                  stroke="var(--color-novera-sheet, #FFFFFF)"
                  strokeWidth={1}
                >
                  {data.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={getChartColor(index)} />
                  ))}
                </Pie>
              </PieChart>
            ) : chart_type === 'line' ? (
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid {...CHART_GRID_STYLE} vertical={false} />
                <XAxis
                  dataKey={x_key}
                  {...CHART_AXIS_STYLE}
                  tickLine={false}
                />
                <YAxis
                  {...CHART_AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatTooltipValue}
                />
                <Tooltip
                  formatter={(value: any) => [formatTooltipValue(value), title]}
                  {...CHART_TOOLTIP_STYLE}
                />
                <Line
                  type="monotone"
                  dataKey={y_key}
                  stroke={primaryColor}
                  strokeWidth={2}
                  dot={{ r: 3, fill: primaryColor, strokeWidth: 1, stroke: '#fff' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            ) : chart_type === 'area' ? (
              <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id={`grad-${chart.id}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={primaryColor} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={primaryColor} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...CHART_GRID_STYLE} vertical={false} />
                <XAxis
                  dataKey={x_key}
                  {...CHART_AXIS_STYLE}
                  tickLine={false}
                />
                <YAxis
                  {...CHART_AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatTooltipValue}
                />
                <Tooltip
                  formatter={(value: any) => [formatTooltipValue(value), title]}
                  {...CHART_TOOLTIP_STYLE}
                />
                <Area
                  type="monotone"
                  dataKey={y_key}
                  stroke={primaryColor}
                  strokeWidth={1.75}
                  fillOpacity={1}
                  fill={`url(#grad-${chart.id})`}
                />
              </AreaChart>
            ) : (
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid {...CHART_GRID_STYLE} vertical={false} />
                <XAxis
                  dataKey={x_key}
                  {...CHART_AXIS_STYLE}
                  tickLine={false}
                />
                <YAxis
                  {...CHART_AXIS_STYLE}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatTooltipValue}
                />
                <Tooltip
                  formatter={(value: any) => [formatTooltipValue(value), title]}
                  {...CHART_TOOLTIP_STYLE}
                />
                <Bar dataKey={y_key} radius={[1, 1, 0, 0]}>
                  {data.map((_, index) => (
                    <Cell
                      key={`bar-cell-${index}`}
                      fill={getChartColor(index)}
                    />
                  ))}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
