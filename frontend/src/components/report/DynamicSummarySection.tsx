import React from 'react'
import {
  Sparkles,
  CheckCircle2,
  TrendingUp,
  BarChart3,
  Scale,
  ShieldCheck,
  AlertCircle,
  Lightbulb,
  ArrowRight,
  Eye,
  Info,
} from 'lucide-react'
import type { DynamicSummarySectionData } from '../../types/report'

interface DynamicSummarySectionProps {
  section: DynamicSummarySectionData
}

export const DynamicSummarySection: React.FC<DynamicSummarySectionProps> = ({ section }) => {
  const { type, title, content, evidence_ids } = section

  // Configuration for technical presentation types
  const getSectionConfig = () => {
    switch (type) {
      case 'executive_takeaway':
        return {
          icon: <Sparkles className="h-4 w-4 text-indigo-600 shrink-0" />,
          containerClass: 'border-indigo-100 bg-gradient-to-br from-indigo-50/50 via-white to-indigo-50/20 text-slate-800',
          titleClass: 'text-indigo-950 font-bold',
          badgeClass: 'bg-indigo-100/70 text-indigo-700',
        }
      case 'finding':
        return {
          icon: <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />,
          containerClass: 'border-emerald-100/80 bg-emerald-50/30 text-slate-800',
          titleClass: 'text-emerald-950 font-semibold',
          badgeClass: 'bg-emerald-100/70 text-emerald-700',
        }
      case 'comparison':
        return {
          icon: <Scale className="h-4 w-4 text-cyan-600 shrink-0" />,
          containerClass: 'border-cyan-100/80 bg-cyan-50/30 text-slate-800',
          titleClass: 'text-cyan-950 font-semibold',
          badgeClass: 'bg-cyan-100/70 text-cyan-700',
        }
      case 'trend':
        return {
          icon: <TrendingUp className="h-4 w-4 text-sky-600 shrink-0" />,
          containerClass: 'border-sky-100/80 bg-sky-50/30 text-slate-800',
          titleClass: 'text-sky-950 font-semibold',
          badgeClass: 'bg-sky-100/70 text-sky-700',
        }
      case 'distribution':
        return {
          icon: <BarChart3 className="h-4 w-4 text-violet-600 shrink-0" />,
          containerClass: 'border-violet-100/80 bg-violet-50/30 text-slate-800',
          titleClass: 'text-violet-950 font-semibold',
          badgeClass: 'bg-violet-100/70 text-violet-700',
        }
      case 'data_quality':
        return {
          icon: <ShieldCheck className="h-4 w-4 text-teal-600 shrink-0" />,
          containerClass: 'border-teal-100/80 bg-teal-50/30 text-slate-800',
          titleClass: 'text-teal-950 font-semibold',
          badgeClass: 'bg-teal-100/70 text-teal-700',
        }
      case 'business_implication':
        return {
          icon: <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" />,
          containerClass: 'border-amber-200/60 bg-amber-50/30 text-slate-800',
          titleClass: 'text-amber-950 font-semibold',
          badgeClass: 'bg-amber-100/70 text-amber-800',
        }
      case 'recommendation':
        return {
          icon: <Lightbulb className="h-4 w-4 text-indigo-600 shrink-0" />,
          containerClass: 'border-indigo-100 bg-white/95 text-slate-800 shadow-2xs',
          titleClass: 'text-indigo-950 font-semibold',
          badgeClass: 'bg-indigo-50 text-indigo-700',
        }
      case 'limitation':
        return {
          icon: <Info className="h-4 w-4 text-slate-500 shrink-0" />,
          containerClass: 'border-slate-200 bg-slate-50 text-slate-700',
          titleClass: 'text-slate-800 font-semibold',
          badgeClass: 'bg-slate-200/70 text-slate-600',
        }
      case 'next_action':
        return {
          icon: <ArrowRight className="h-4 w-4 text-blue-600 shrink-0" />,
          containerClass: 'border-blue-100 bg-blue-50/40 text-slate-800',
          titleClass: 'text-blue-950 font-semibold',
          badgeClass: 'bg-blue-100 text-blue-700',
        }
      case 'observation':
      default:
        return {
          icon: <Eye className="h-4 w-4 text-slate-600 shrink-0" />,
          containerClass: 'border-slate-200/80 bg-white text-slate-800',
          titleClass: 'text-slate-900 font-semibold',
          badgeClass: 'bg-slate-100 text-slate-700',
        }
    }
  }

  const config = getSectionConfig()

  return (
    <div className={`rounded-xl border p-4 space-y-2 transition-all hover:shadow-xs ${config.containerClass}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {config.icon}
          <h4 className={`text-xs uppercase tracking-wider ${config.titleClass}`}>
            {title || type.replace('_', ' ')}
          </h4>
        </div>
        {evidence_ids && evidence_ids.length > 0 && (
          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${config.badgeClass}`}>
            {evidence_ids.length} verified {evidence_ids.length === 1 ? 'evidence' : 'evidences'}
          </span>
        )}
      </div>

      <p className="text-xs leading-relaxed font-normal whitespace-pre-line text-slate-700 pl-6">
        {content}
      </p>
    </div>
  )
}
