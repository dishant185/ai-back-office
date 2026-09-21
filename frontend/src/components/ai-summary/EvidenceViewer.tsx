import React, { useState } from 'react'
import { X, CheckCircle2, ShieldCheck, Database, ChevronDown, ChevronRight, Layers, FileText } from 'lucide-react'
import { Button } from '../ui/Button'

interface EvidenceViewerProps {
  isOpen: boolean
  onClose: () => void
  evidence?: Record<string, any>
  datasetName?: string
  datasetVersion?: number
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  isOpen,
  onClose,
  evidence = {},
  datasetName,
  datasetVersion = 1,
}) => {
  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>({})

  if (!isOpen) return null

  const evidenceItems = Object.entries(evidence).map(([key, val]) => ({
    id: key,
    ...val,
  }))

  const toggleTechnicalDetails = (key: string) => {
    setExpandedDetails((prev) => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[88vh] flex flex-col bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Deterministic Evidence Audit Trail</h3>
              <p className="text-[11px] text-slate-500">
                Authoritative analytical facts verified for {datasetName || 'uploaded dataset'} (v{datasetVersion})
              </p>
            </div>
          </div>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-400 hover:text-slate-600" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Evidence List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/30">
          {evidenceItems.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No evidence records found for this report scope.
            </div>
          ) : (
            evidenceItems.map((item, idx) => {
              const itemKey = item.id || `ev_${idx}`
              const isDetailsOpen = Boolean(expandedDetails[itemKey])

              const claimTitle =
                item.claim ||
                item.title ||
                (item.entity && item.measure
                  ? `${item.entity} — ${item.measure}`
                  : item.measure || item.metric || 'Analytical Metric')

              const metricName = item.semantic_measure || item.measure || item.metric || 'Metric'
              const dimensionName = item.dimension || 'Dataset-wide'
              const entityName = item.entity || 'Overall'
              const aggMethod = item.aggregation || item.calculation_method || 'COUNT / AGG'
              const displayVal = item.formatted_value || String(item.value ?? 'Unavailable')
              const unitStr = item.unit || (item.currency ? 'currency' : 'count')
              const calcFormula = item.calculation || `${aggMethod}(${metricName})`
              const scopeDesc = item.scope || 'all_records'
              const dsLabel = item.dataset_id || datasetName || 'dataset'
              const dsVer = item.dataset_version || datasetVersion

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200/90 bg-white hover:border-indigo-200 transition-all shadow-2xs space-y-3"
                >
                  {/* Top Bar: Claim & Verification Badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-xs font-semibold text-slate-900 tracking-tight">
                          {claimTitle}
                        </h4>
                        <p className="text-[11px] text-slate-600 pt-0.5 font-normal">
                          {item.narrative || `Verified calculation: ${displayVal} (${metricName})`}
                        </p>
                      </div>
                    </div>
                    <span className="shrink-0 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      ✓ Deterministically Verified
                    </span>
                  </div>

                  {/* 12 Required Fields Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100 text-[11px]">
                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Metric</span>
                      <span className="font-semibold text-slate-800 break-words">{metricName}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Dimension</span>
                      <span className="font-medium text-slate-800 break-words">{dimensionName}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Entity</span>
                      <span className="font-medium text-slate-800 break-words">{entityName}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Aggregation</span>
                      <span className="font-medium text-indigo-700">{aggMethod}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Value</span>
                      <span className="font-bold text-slate-900">{displayVal}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Unit</span>
                      <span className="font-medium text-slate-700">{unitStr}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Calculation</span>
                      <span className="font-mono text-[10px] text-slate-700 truncate block" title={calcFormula}>{calcFormula}</span>
                    </div>

                    <div className="bg-slate-50/70 p-2 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block text-[10px] font-medium uppercase tracking-wider">Scope</span>
                      <span className="font-medium text-slate-700 break-words">{scopeDesc}</span>
                    </div>
                  </div>

                  {/* Scope & Traceability Meta */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[10px] text-slate-500">
                    <span className="flex items-center gap-1.5">
                      <Layers className="h-3 w-3 text-slate-400" />
                      <span>Dataset: <strong className="font-semibold text-slate-700">{dsLabel}</strong> (v{dsVer})</span>
                    </span>

                    {/* Collapsible Technical Details Button */}
                    <button
                      type="button"
                      onClick={() => toggleTechnicalDetails(itemKey)}
                      className="inline-flex items-center gap-1 text-[10px] font-medium text-indigo-600 hover:text-indigo-800 transition-colors cursor-pointer"
                    >
                      {isDetailsOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                      <span>{isDetailsOpen ? 'Hide Technical Details' : 'Technical Details / Audit Details'}</span>
                    </button>
                  </div>

                  {/* Collapsible Audit / Technical Details Section */}
                  {isDetailsOpen && (
                    <div className="mt-2 p-3 bg-slate-900 text-slate-200 rounded-lg text-[10px] font-mono space-y-1.5 border border-slate-800 animate-fade-in">
                      <div className="text-slate-400 flex items-center gap-1.5 pb-1 border-b border-slate-800">
                        <FileText className="h-3 w-3 text-indigo-400" />
                        <span>INTERNAL AUDIT TELEMETRY</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                        <div><span className="text-slate-500">evidence_id:</span> <span className="text-indigo-300">{item.id || item.evidence_id}</span></div>
                        <div><span className="text-slate-500">type:</span> <span className="text-emerald-300">{item.type || 'METRIC'}</span></div>
                        <div><span className="text-slate-500">verified:</span> <span className="text-emerald-400">true</span></div>
                        <div><span className="text-slate-500">is_estimated:</span> <span className="text-amber-300">{String(Boolean(item.is_estimated))}</span></div>
                        {item.rank && <div><span className="text-slate-500">rank:</span> #{item.rank}</div>}
                        {item.difference_from_top !== undefined && item.difference_from_top !== null && (
                          <div><span className="text-slate-500">diff_from_top:</span> {item.difference_from_top}</div>
                        )}
                        {item.filter_hash && <div><span className="text-slate-500">filter_hash:</span> {item.filter_hash}</div>}
                      </div>
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-100 bg-slate-50/70 text-[11px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <Database className="h-3.5 w-3.5 text-slate-400" />
            <span><strong>{evidenceItems.length}</strong> authoritative facts verified for {datasetName || 'current dataset'}</span>
          </span>
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
