import React from 'react'
import { X, CheckCircle2, ShieldCheck, Database } from 'lucide-react'
import { StatusStamp } from './StatusStamp'
import { cn } from '../../lib/utils'

export interface EvidenceRecord {
  claim: string
  dataset?: string
  version?: string | number
  measure?: string
  aggregation?: string
  entity?: string
  value?: string | number
  rank?: string | number
  scope?: string
  calculation?: string
  status?: string
}

interface EvidenceDrawerProps {
  isOpen: boolean
  onClose: () => void
  evidence: EvidenceRecord | null
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  evidence,
}) => {
  if (!isOpen || !evidence) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-novera-ink/40 backdrop-blur-[2px] transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-novera-paper-sheet border-l border-novera-rule shadow-2xl flex flex-col animate-slide-up sm:animate-none">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-novera-rule bg-novera-paper-sunken/40">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-[1px] bg-novera-green" />
            <h2 className="text-sm font-semibold tracking-tight uppercase text-novera-ink">
              Evidence Inspector
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-[2px] text-novera-muted hover:text-novera-ink hover:bg-novera-paper-sunken transition-colors cursor-pointer"
            aria-label="Close inspector"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
          {/* Claim Box */}
          <div className="p-3.5 bg-novera-paper rounded-[2px] border border-novera-rule space-y-1.5">
            <span className="text-[10px] font-mono uppercase tracking-wider text-novera-muted font-semibold">
              Audited Analytical Statement
            </span>
            <p className="text-sm font-medium text-novera-ink leading-relaxed">
              "{evidence.claim}"
            </p>
          </div>

          {/* Verification Audit Stamp */}
          <div className="flex items-center justify-between py-2 border-b border-novera-rule">
            <span className="text-novera-muted font-medium">Audit Verification</span>
            <StatusStamp status={evidence.status || 'VERIFIED'} />
          </div>

          {/* Detailed Ledger Attributes */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-novera-muted font-semibold block">
              Provenance Ledger Details
            </span>

            <div className="divide-y divide-novera-rule border border-novera-rule rounded-[2px] bg-novera-paper-sheet">
              <div className="flex items-center justify-between p-3">
                <span className="text-novera-secondary">Dataset Source</span>
                <span className="font-mono text-novera-ink font-medium truncate max-w-[200px]">
                  {evidence.dataset || 'Active Ingested Dataset'}
                </span>
              </div>

              {evidence.version && (
                <div className="flex items-center justify-between p-3">
                  <span className="text-novera-secondary">Dataset Version</span>
                  <span className="font-mono text-novera-ink">v{evidence.version}</span>
                </div>
              )}

              {evidence.measure && (
                <div className="flex items-center justify-between p-3">
                  <span className="text-novera-secondary">Calculated Measure</span>
                  <span className="font-mono text-novera-ink font-medium">{evidence.measure}</span>
                </div>
              )}

              {evidence.aggregation && (
                <div className="flex items-center justify-between p-3">
                  <span className="text-novera-secondary">Aggregation Function</span>
                  <span className="font-mono text-novera-ink bg-novera-paper-sunken px-1.5 py-0.5 rounded-[2px]">
                    {evidence.aggregation}
                  </span>
                </div>
              )}

              {evidence.entity && (
                <div className="flex items-center justify-between p-3">
                  <span className="text-novera-secondary">Segment / Entity</span>
                  <span className="font-mono text-novera-ink font-medium">{evidence.entity}</span>
                </div>
              )}

              {evidence.value !== undefined && (
                <div className="flex items-center justify-between p-3 bg-novera-paper/40">
                  <span className="text-novera-ink font-semibold">Verified Numeric Value</span>
                  <span className="font-mono font-bold text-novera-green text-sm tabular-nums">
                    {String(evidence.value)}
                  </span>
                </div>
              )}

              {evidence.rank && (
                <div className="flex items-center justify-between p-3">
                  <span className="text-novera-secondary">Relative Distribution Rank</span>
                  <span className="font-mono text-novera-ink font-medium">#{evidence.rank}</span>
                </div>
              )}

              {evidence.calculation && (
                <div className="p-3 space-y-1">
                  <span className="text-novera-secondary block">Calculation Routine</span>
                  <code className="block font-mono text-[11px] text-novera-ink bg-novera-paper p-2 rounded-[2px] break-all border border-novera-rule">
                    {evidence.calculation}
                  </code>
                </div>
              )}
            </div>
          </div>

          <div className="p-3 bg-novera-paper-sunken/40 rounded-[2px] border border-novera-rule text-[11px] text-novera-muted leading-relaxed">
            Every insight in Novera traces directly back to row-level execution. No generative AI model is permitted to author or alter verified mathematical numbers.
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-novera-rule bg-novera-paper flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-novera-ink bg-novera-paper-sheet border border-novera-rule rounded-[2px] hover:bg-novera-paper-sunken transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </>
  )
}
