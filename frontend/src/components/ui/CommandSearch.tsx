import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Database, FileText, BarChart3, Plus, ArrowRight, ShieldCheck, X } from 'lucide-react'

interface CommandItem {
  id: string
  title: string
  subtitle: string
  category: 'Datasets' | 'Reports' | 'Metrics' | 'Actions'
  icon: React.ComponentType<{ className?: string }>
  route: string
}

const COMMAND_ITEMS: CommandItem[] = [
  // Actions
  {
    id: 'upload',
    title: 'Upload dataset',
    subtitle: 'Import CSV or Excel spreadsheet for verified profiling',
    category: 'Actions',
    icon: Plus,
    route: '/upload',
  },
  {
    id: 'create-report',
    title: 'Generate executive report',
    subtitle: 'Run deterministic analytics and management brief',
    category: 'Actions',
    icon: FileText,
    route: '/reports',
  },
  {
    id: 'ask-analyst',
    title: 'Ask Novera Analyst',
    subtitle: 'Conversational business intelligence with row-level proof',
    category: 'Actions',
    icon: ShieldCheck,
    route: '/ai-analyst',
  },
  // Datasets
  {
    id: 'datasets-registry',
    title: 'Datasets registry',
    subtitle: 'Manage ingested spreadsheets and schema versions',
    category: 'Datasets',
    icon: Database,
    route: '/upload',
  },
  {
    id: 'data-mapping',
    title: 'Data mapping studio',
    subtitle: 'Harmonize column parameters to canonical ontology',
    category: 'Datasets',
    icon: Database,
    route: '/mapping',
  },
  // Reports
  {
    id: 'reports-archive',
    title: 'Executive reports archive',
    subtitle: 'Corporate MIS reports and ReportLab PDF downloads',
    category: 'Reports',
    icon: FileText,
    route: '/reports',
  },
  // Metrics
  {
    id: 'metric-revenue',
    title: 'Revenue analytics',
    subtitle: 'Total gross proceeds and distribution by region/product',
    category: 'Metrics',
    icon: BarChart3,
    route: '/analytics',
  },
  {
    id: 'metric-quality',
    title: 'Data quality audit',
    subtitle: 'Completeness scores, duplicates, and anomaly log',
    category: 'Metrics',
    icon: ShieldCheck,
    route: '/quality',
  },
]

export const CommandSearch: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        if (isOpen) {
          onClose()
        } else {
          // Open handled by parent or shortcut listener
        }
      } else if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const filtered = COMMAND_ITEMS.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.subtitle.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
  )

  const handleSelect = (route: string) => {
    navigate(route)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-novera-ink/50 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Box */}
      <div className="relative w-full max-w-xl bg-novera-paper-sheet border border-novera-rule shadow-2xl rounded-[2px] overflow-hidden animate-slide-up">
        {/* Search Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-novera-rule bg-novera-paper-sheet">
          <Search className="h-4 w-4 text-novera-muted shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            placeholder="Search datasets, reports, metrics, actions... (ESC to close)"
            className="w-full bg-transparent text-sm text-novera-ink placeholder:text-novera-muted outline-none font-sans"
          />
          <button
            type="button"
            onClick={onClose}
            className="p-1 text-novera-muted hover:text-novera-ink rounded-[2px] cursor-pointer"
            aria-label="Close search"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto divide-y divide-novera-rule/50 p-2">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-xs text-novera-muted font-mono">
              No matching records found for "{query}"
            </div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon
              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item.route)}
                  className="group flex items-center justify-between p-2.5 rounded-[2px] hover:bg-novera-paper cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[2px] bg-novera-paper-sunken text-novera-secondary group-hover:text-novera-green transition-colors">
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-novera-ink group-hover:text-novera-green transition-colors truncate">
                        {item.title}
                      </p>
                      <p className="text-[11px] text-novera-muted truncate">{item.subtitle}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className="font-mono text-[10px] uppercase text-novera-muted bg-novera-paper-sunken px-1.5 py-0.5 rounded-[1px]">
                      {item.category}
                    </span>
                    <ArrowRight className="h-3 w-3 text-novera-muted group-hover:text-novera-ink transition-transform group-hover:translate-x-0.5" />
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-4 py-2 border-t border-novera-rule bg-novera-paper-sunken/40 flex items-center justify-between text-[11px] text-novera-muted font-mono">
          <span>Novera Control Desk</span>
          <span>Press Enter to select</span>
        </div>
      </div>
    </div>
  )
}
