import React from 'react'
import { Sparkles, Copy, Check, FileText, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { Button } from '../ui/Button'
import { AIStatusBadge } from './AIStatusBadge'

interface SummaryHeaderProps {
  title: string
  status?: string
  isExpanded: boolean
  copied: boolean
  isLoading?: boolean
  onToggleExpand: () => void
  onCopy: () => void
  onViewEvidence?: () => void
  onRegenerate?: () => void
}

export const SummaryHeader: React.FC<SummaryHeaderProps> = ({
  title,
  status,
  isExpanded,
  copied,
  isLoading = false,
  onToggleExpand,
  onCopy,
  onViewEvidence,
  onRegenerate,
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-indigo-100/80">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs shrink-0">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider">
              {status?.toUpperCase() === 'AI_GENERATED_GROUNDED' ? 'AI Executive Summary' : 'Verified Analytics Summary'}
            </span>
            <AIStatusBadge status={status} />
          </div>
          <h3 className="text-sm sm:text-base font-bold text-indigo-950 mt-0.5">{title}</h3>
        </div>
      </div>

      {/* Action Buttons: Copy Clean Summary, View Evidence, Regenerate, Collapse */}
      <div className="flex items-center gap-1.5 self-end sm:self-auto">
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-[11px] px-2.5 gap-1.5 border-indigo-200 text-indigo-800 hover:bg-indigo-50"
          onClick={onCopy}
          title="Copy clean executive text"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
          <span>{copied ? 'Copied' : 'Copy Summary'}</span>
        </Button>

        {onViewEvidence && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-[11px] px-2.5 gap-1.5 border-indigo-200 text-indigo-800 hover:bg-indigo-50"
            onClick={onViewEvidence}
            title="Audit verified evidence trail"
          >
            <FileText className="h-3 w-3" />
            <span>View Evidence</span>
          </Button>
        )}

        {onRegenerate && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-[11px] px-2.5 gap-1.5 border-indigo-200 text-indigo-800 hover:bg-indigo-50"
            onClick={onRegenerate}
            disabled={isLoading}
            title="Regenerate summary from current analytics"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Regenerate</span>
          </Button>
        )}

        <button
          type="button"
          className="flex h-7 w-7 items-center justify-center rounded-lg text-indigo-600 hover:bg-indigo-100/60 transition cursor-pointer"
          onClick={onToggleExpand}
          aria-label={isExpanded ? 'Collapse summary' : 'Expand summary'}
        >
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  )
}
