/**
 * SuggestedQuestions — Profile-aware question suggestions.
 */
import { ChevronRight, Sparkles } from 'lucide-react'
import type { SuggestedQuestion } from '../../types/ai'

const QUESTIONS_BY_PROFILE: Record<string, SuggestedQuestion[]> = {
  sales: [
    { category: 'Sales', title: 'What are total sales?', query: 'What are total sales?' },
    { category: 'Regional', title: 'Which region has the highest sales?', query: 'Which region has the highest sales?' },
    { category: 'Product', title: 'What products sell the most?', query: 'What products sell the most?' },
    { category: 'Channels', title: 'What sales channels are available?', query: 'What sales channels are available?' },
    { category: 'Data Quality', title: 'Are there duplicate records?', query: 'Are there duplicate records?' },
  ],
  hr: [
    { category: 'Workforce', title: 'How many employees are there?', query: 'How many employees are there?' },
    { category: 'Demographics', title: 'What is the average age?', query: 'What is the average age?' },
    { category: 'Location', title: 'Which city has the most employees?', query: 'Which city has the most employees?' },
    { category: 'Attrition', title: 'What is the attrition rate?', query: 'What is the attrition rate?' },
    { category: 'Data Quality', title: 'Are there duplicate records?', query: 'Are there duplicate records?' },
  ],
  inventory: [
    { category: 'Stock', title: 'Which products are low in stock?', query: 'Which products are low in stock?' },
    { category: 'Risk', title: 'What inventory risks exist?', query: 'What inventory risks should I focus on?' },
    { category: 'Movement', title: 'Highest inventory movement?', query: 'Which products have the highest movement?' },
  ],
  finance: [
    { category: 'Expense', title: 'What are the top expenses?', query: 'What are the largest expense categories?' },
    { category: 'Overview', title: 'Summarize financial health', query: 'Summarize the financial health of this dataset.' },
  ],
  customer: [
    { category: 'Segments', title: 'What are the customer segments?', query: 'What are the main customer segments?' },
    { category: 'Retention', title: 'What drives customer retention?', query: 'What drives customer retention?' },
  ],
  generic: [
    { category: 'Overview', title: 'Summarize this dataset', query: 'Summarize the key insights from this dataset.' },
    { category: 'Analysis', title: 'What patterns exist?', query: 'What patterns are visible in this data?' },
    { category: 'Metrics', title: 'What are the key metrics?', query: 'What are the most important metrics?' },
  ],
}

interface SuggestedQuestionsProps {
  profile: string
  onSelect: (query: string) => void
  compact?: boolean
}

export function SuggestedQuestions({ profile, onSelect, compact = false }: SuggestedQuestionsProps) {
  const questions = QUESTIONS_BY_PROFILE[profile] || QUESTIONS_BY_PROFILE.generic

  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {questions.slice(0, 4).map((q) => (
          <button
            key={q.query}
            type="button"
            onClick={() => onSelect(q.query)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
          >
            {q.title}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 px-1">
        <Sparkles className="h-3.5 w-3.5 text-brand-500" />
        <span className="text-xs font-semibold text-slate-500">Suggested Questions</span>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {questions.map((q) => (
          <button
            key={q.query}
            type="button"
            onClick={() => onSelect(q.query)}
            className="group flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-left transition-all hover:border-brand-300 hover:bg-brand-50/50 hover:shadow-sm"
          >
            <div className="min-w-0">
              <p className="text-[10px] font-bold uppercase tracking-wider text-brand-500">{q.category}</p>
              <p className="text-xs font-semibold text-slate-700 group-hover:text-brand-700 truncate">{q.title}</p>
            </div>
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-500" />
          </button>
        ))}
      </div>
    </div>
  )
}
