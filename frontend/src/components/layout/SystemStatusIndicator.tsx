import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { healthService } from '../../services/api'
import { Database, Cpu, CheckCircle2, AlertCircle, RefreshCw, XCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

export const SystemStatusIndicator: React.FC<{ className?: string }> = ({ className }) => {
  const [showDetails, setShowDetails] = useState(false)

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['system-readiness'],
    queryFn: healthService.getReadiness,
    refetchInterval: 30000,
    retry: 2,
  })

  // State derivation
  let statusColor = 'bg-slate-400'
  let statusText = 'Checking connectivity...'
  if (isLoading) {
    statusColor = 'bg-slate-400 animate-pulse'
    statusText = 'Checking system...'
  } else if (isError || !data) {
    statusColor = 'bg-rose-500'
    statusText = 'Backend Offline'
  } else {
    const dbOk = data.database?.connected
    const llmOk = data.llm?.connected
    const llmStatus = data.llm?.status

    if (dbOk && llmOk) {
      statusColor = 'bg-emerald-500'
      statusText = 'Systems Operational'
    } else if (dbOk && (llmStatus === 'not_configured' || !llmOk)) {
      statusColor = 'bg-amber-500'
      statusText = 'AI Offline • Analytics Ready'
    } else {
      statusColor = 'bg-rose-500'
      statusText = 'Degraded Performance'
    }
  }

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setShowDetails((prev) => !prev)}
        className="w-full group flex items-center justify-between px-2.5 py-1.5 rounded-[2px] text-xs font-mono border border-novera-rule/40 dark:border-white/10 bg-novera-ink/50 hover:bg-novera-ink/80 text-novera-secondary dark:text-novera-dark-secondary hover:text-white transition-colors cursor-pointer"
        title="Click to view backend system telemetry"
        aria-label="System status telemetry"
        aria-expanded={showDetails}
      >
        <div className="flex items-center gap-2 truncate">
          <span className={cn('inline-block h-2 w-2 rounded-[1px]', statusColor)} />
          <span className="truncate tracking-tight font-sans text-xs">{statusText}</span>
        </div>
        <span className="text-[10px] font-mono text-novera-muted group-hover:text-novera-secondary transition-colors">
          {data?.version ? `v${data.version}` : ''}
        </span>
      </button>

      {/* Popover Card */}
      {showDetails && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowDetails(false)}
          />
          <div className="absolute bottom-full left-0 mb-2 w-64 p-3 rounded-[2px] bg-novera-sheet dark:bg-novera-dark-sheet border border-novera-rule dark:border-white/10 shadow-lg z-50 text-xs space-y-2.5">
            <div className="flex items-center justify-between border-b border-novera-rule dark:border-white/10 pb-2">
              <span className="font-semibold text-novera-ink dark:text-novera-dark-ink font-sans">Telemetry Status</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  refetch()
                }}
                className="text-novera-muted hover:text-novera-ink dark:hover:text-white transition-colors p-0.5"
                title="Refresh health status"
                aria-label="Refresh telemetry"
              >
                <RefreshCw className={cn('h-3 w-3', isFetching && 'animate-spin')} />
              </button>
            </div>

            {isError ? (
              <div className="flex items-start gap-2 text-novera-flag text-[11px]">
                <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium">Backend unreachable</div>
                  <div className="text-novera-muted mt-0.5">
                    {(error as Error)?.message || 'Failed to connect to API server.'}
                  </div>
                </div>
              </div>
            ) : data ? (
              <div className="space-y-2">
                {/* Database */}
                <div className="flex items-center justify-between font-mono text-xs">
                  <div className="flex items-center gap-1.5 text-novera-secondary dark:text-novera-dark-secondary">
                    <Database className="h-3.5 w-3.5 text-novera-muted" />
                    <span>Database</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {data.database?.connected ? (
                      <span className="text-novera-green dark:text-novera-green-light flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Connected
                      </span>
                    ) : (
                      <span className="text-novera-flag flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> Disconnected
                      </span>
                    )}
                  </div>
                </div>

                {/* LLM Engine */}
                <div className="flex items-center justify-between font-mono text-xs">
                  <div className="flex items-center gap-1.5 text-novera-secondary dark:text-novera-dark-secondary">
                    <Cpu className="h-3.5 w-3.5 text-novera-muted" />
                    <span>AI Engine</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {data.llm?.connected ? (
                      <span className="text-novera-green dark:text-novera-green-light flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Grounded
                      </span>
                    ) : (
                      <span className="text-novera-brass flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> {data.llm?.status || 'Offline'}
                      </span>
                    )}
                  </div>
                </div>

                {/* Model & Provider Info */}
                {data.llm?.details && (
                  <div className="pt-1.5 border-t border-novera-rule dark:border-white/10 text-[10px] text-novera-muted flex flex-col gap-0.5 font-mono">
                    <div className="truncate">
                      Provider: {data.llm.details.provider || 'unknown'}
                    </div>
                    <div className="truncate">
                      Model: {data.llm.details.model || 'none'}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  )
}
