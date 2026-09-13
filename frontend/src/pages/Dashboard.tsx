import {
  Activity,
  ArrowRight,
  CircleAlert,
  CircleCheckBig,
  Database,
  FileSpreadsheet,
  Server,
  Signal,
  Sparkles,
  Upload,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { StatCard } from '../components/ui/StatCard'
import { healthService } from '../services/api'

const quickActions = [
  {
    title: 'Upload Data',
    description: 'Import CSV or Excel files for analysis',
    icon: Upload,
    href: '/upload',
    color: 'bg-brand-50 text-brand-600',
  },
  {
    title: 'View Reports',
    description: 'Browse generated business insights',
    icon: FileSpreadsheet,
    href: '/reports',
    color: 'bg-violet-50 text-violet-600',
  },
  {
    title: 'AI Analyst',
    description: 'Ask questions about your data',
    icon: Sparkles,
    href: '/ai-analyst',
    color: 'bg-emerald-50 text-emerald-600',
  },
]

function Dashboard() {
  const { isLoading, isError, data, refetch } = useQuery({
    queryKey: ['health'],
    queryFn: healthService.getHealth,
    retry: false,
  })

  const apiStatusText = isLoading ? 'Checking...' : isError ? 'Offline' : data?.status ?? 'Healthy'

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Dashboard"
        title="AI Back-Office Copilot"
        description="Monitor system health, manage data uploads, and access AI-powered business insights."
      />

      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Datasets" value="—" icon={Database} trend={{ value: 'Upload to begin' }} />
        <StatCard
          label="Reports"
          value="0"
          icon={FileSpreadsheet}
          iconClassName="bg-violet-50 text-violet-600"
        />
        <StatCard
          label="AI Queries"
          value="0"
          icon={Sparkles}
          iconClassName="bg-emerald-50 text-emerald-600"
        />
        <StatCard
          label="API Status"
          value={isLoading ? '...' : isError ? 'Offline' : 'Online'}
          icon={Activity}
          iconClassName={
            isError ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'
          }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* System Status */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">System Status</h2>
                <p className="text-sm text-slate-500">Real-time service health monitoring</p>
              </div>
              <Badge variant="brand" dot>
                Live
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/80 p-4 transition hover:border-emerald-200 hover:bg-emerald-50/30">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600">
                  <Signal className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">Frontend</p>
                  <p className="text-xs text-slate-500">React + Vite</p>
                </div>
              </div>
              <Badge variant="success" dot>
                Running
              </Badge>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/80 p-4 transition hover:border-slate-200">
              <div className="flex items-center gap-3">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                    isError ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  <Server className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">Backend API</p>
                  <p className="text-xs text-slate-500">FastAPI server</p>
                </div>
              </div>
              {isLoading ? (
                <Badge variant="warning" dot>
                  Checking
                </Badge>
              ) : isError ? (
                <Badge variant="error" dot>
                  Offline
                </Badge>
              ) : (
                <Badge variant="success" dot>
                  Connected
                </Badge>
              )}
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="font-semibold text-slate-800">Health Check</span>
                {isLoading ? (
                  <Badge variant="warning">Pending</Badge>
                ) : isError ? (
                  <Badge variant="error">Failed</Badge>
                ) : (
                  <Badge variant="success">Passed</Badge>
                )}
              </div>

              {isLoading ? (
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Activity className="h-4 w-4 animate-pulse" />
                  Waiting for API health response...
                </div>
              ) : isError ? (
                <div className="space-y-3">
                  <div className="flex items-start gap-2 text-sm text-red-700">
                    <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                    <div>
                      <p className="font-medium">Unable to connect to the backend.</p>
                      <p className="mt-0.5 text-red-600/80">
                        Please check that the API server is running.
                      </p>
                    </div>
                  </div>
                  <Button variant="danger" size="sm" onClick={() => void refetch()}>
                    Retry connection
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <CircleCheckBig className="h-4 w-4 text-emerald-600" />
                  {apiStatusText}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-bold text-slate-900">Quick Actions</h2>
            <p className="text-sm text-slate-500">Get started quickly</p>
          </CardHeader>
          <CardContent className="space-y-2">
            {quickActions.map(({ title, description, icon: Icon, href, color }) => (
              <Link
                key={title}
                to={href}
                className="group flex items-center gap-3 rounded-xl border border-slate-100 p-3 transition-all duration-200 hover:border-brand-200 hover:bg-brand-50/30 hover:shadow-sm"
              >
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${color}`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-800">{title}</p>
                  <p className="truncate text-xs text-slate-500">{description}</p>
                </div>
                <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-500" />
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
