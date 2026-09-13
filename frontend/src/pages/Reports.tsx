import {
  BarChart3,
  Calendar,
  Download,
  FileText,
  Filter,
  LineChart,
  PieChart,
  TrendingUp,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'

const reportTypes = [
  {
    title: 'Revenue Analysis',
    description: 'Monthly revenue trends, growth rates, and forecasting',
    icon: TrendingUp,
    status: 'Coming soon',
    color: 'bg-emerald-50 text-emerald-600',
  },
  {
    title: 'Expense Breakdown',
    description: 'Category-wise expense distribution and anomalies',
    icon: PieChart,
    status: 'Coming soon',
    color: 'bg-violet-50 text-violet-600',
  },
  {
    title: 'Performance Metrics',
    description: 'KPI dashboards with period-over-period comparison',
    icon: BarChart3,
    status: 'Coming soon',
    color: 'bg-brand-50 text-brand-600',
  },
  {
    title: 'Trend Forecast',
    description: 'AI-powered predictions based on historical data',
    icon: LineChart,
    status: 'Coming soon',
    color: 'bg-sky-50 text-sky-600',
  },
]

function Reports() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Reports"
        title="Business Reports"
        description="Generate and explore AI-powered insights from your uploaded business data."
        actions={
          <>
            <Button variant="secondary" size="sm">
              <Filter className="h-4 w-4" />
              Filter
            </Button>
            <Button variant="secondary" size="sm">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </>
        }
      />

      {/* Empty state hero */}
      <Card className="overflow-hidden">
        <div className="relative px-6 py-12 text-center sm:px-12 sm:py-16">
          <div className="pointer-events-none absolute inset-0 gradient-mesh opacity-50" />
          <div className="relative">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
              <FileText className="h-8 w-8" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 sm:text-2xl">No reports yet</h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
              Upload your business data to automatically generate revenue, expense, and
              performance reports powered by AI.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Link to="/upload">
                <Button type="button">Upload data</Button>
              </Link>
              <Badge variant="info">
                <Calendar className="mr-1 h-3 w-3" />
                Phase 2 feature
              </Badge>
            </div>
          </div>
        </div>
      </Card>

      {/* Report types grid */}
      <div>
        <h2 className="mb-4 text-lg font-bold text-slate-900">Available Report Types</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {reportTypes.map(({ title, description, icon: Icon, status, color }) => (
            <Card key={title} hover className="group">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <Badge variant="default">{status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <h3 className="font-semibold text-slate-900">{title}</h3>
                <p className="mt-1 text-sm text-slate-500">{description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Reports
