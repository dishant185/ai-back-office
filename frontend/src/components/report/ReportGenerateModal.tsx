import { useEffect, useState } from 'react'
import {
  AlertCircle,
  Calendar,
  Filter,
  FileText,
  Loader2,
  Lock,
  Sparkles,
  X,
} from 'lucide-react'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { reportService } from '../../services/reportService'
import type { ReportTypeStatus } from '../../types/report'

interface ReportGenerateModalProps {
  isOpen: boolean
  onClose: () => void
  currentDatasetId: string
  datasetList: Array<{ id: string; name: string; profile?: string; row_count?: number }>
  onGenerate: (datasetId: string, reportType: string, filters: Record<string, any>) => Promise<void>
}

export const ReportGenerateModal: React.FC<ReportGenerateModalProps> = ({
  isOpen,
  onClose,
  currentDatasetId,
  datasetList,
  onGenerate,
}) => {
  const [selectedDatasetId, setSelectedDatasetId] = useState(currentDatasetId)
  const [reportTypes, setReportTypes] = useState<ReportTypeStatus[]>([])
  const [selectedType, setSelectedType] = useState<string>('standard')
  const [loadingTypes, setLoadingTypes] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filters state
  const [dateFilter, setDateFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')

  useEffect(() => {
    if (currentDatasetId) {
      setSelectedDatasetId(currentDatasetId)
    }
  }, [currentDatasetId])

  useEffect(() => {
    if (!isOpen || !selectedDatasetId) return

    const fetchTypes = async () => {
      setLoadingTypes(true)
      setError(null)
      try {
        const types = await reportService.getSupportedTypes(selectedDatasetId)
        setReportTypes(types)
        const firstAvail = types.find((t) => t.available)
        if (firstAvail) {
          setSelectedType(firstAvail.key)
        } else {
          setSelectedType('standard')
        }
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to detect supported report types.')
      } finally {
        setLoadingTypes(false)
      }
    }

    void fetchTypes()
  }, [isOpen, selectedDatasetId])

  if (!isOpen) return null

  const handleRunGenerate = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const filters: Record<string, any> = {}
      if (dateFilter) filters.date = dateFilter
      if (categoryFilter) filters.category = categoryFilter

      await onGenerate(selectedDatasetId, selectedType, filters)
      onClose()
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate report.')
    } finally {
      setSubmitting(false)
    }
  }

  const selectedDef = reportTypes.find((t) => t.key === selectedType)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fade-in">
      <Card className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="border-b border-slate-100 bg-slate-50/70 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Generate MIS Report</h2>
              <p className="text-xs text-slate-500">Capability-aware deterministic business reporting</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && (
            <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {/* Dataset Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Source Dataset</label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs font-semibold text-slate-800 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
            >
              {datasetList.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} {d.row_count ? `(${d.row_count.toLocaleString()} rows)` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Report Type Selector */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700">Select Report Type</label>
              <span className="text-[11px] text-slate-400">Filtered by dataset capabilities</span>
            </div>

            {loadingTypes ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
                <span className="ml-2 text-xs font-semibold text-slate-500">Checking dataset capabilities...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-56 overflow-y-auto pr-1">
                {reportTypes.map((rt) => {
                  const isSelected = selectedType === rt.key
                  const isAvail = rt.available

                  return (
                    <button
                      key={rt.key}
                      type="button"
                      disabled={!isAvail}
                      onClick={() => isAvail && setSelectedType(rt.key)}
                      className={`text-left p-3 rounded-xl border transition flex flex-col justify-between ${
                        isSelected
                          ? 'border-brand-500 bg-brand-50/50 shadow-sm'
                          : isAvail
                          ? 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                          : 'border-slate-100 bg-slate-50/60 opacity-50 cursor-not-allowed'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-1.5">
                        <span className="text-xs font-bold text-slate-900">{rt.title}</span>
                        {isAvail ? (
                          <span className="shrink-0 rounded-md bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                            Available
                          </span>
                        ) : (
                          <span className="shrink-0 flex items-center gap-0.5 rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                            <Lock className="h-2.5 w-2.5" />
                            Locked
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">{rt.description}</p>
                      {!isAvail && rt.missing_capabilities.length > 0 && (
                        <p className="text-[10px] text-amber-600 mt-1 font-mono">
                          Missing: {rt.missing_capabilities.slice(0, 2).join(', ')}
                        </p>
                      )}
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Selected Report Details & Optional Filters */}
          {selectedDef && (
            <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand-600" />
                <h3 className="text-xs font-bold text-slate-800">{selectedDef.title} Parameters</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 flex items-center gap-1">
                    <Calendar className="h-3 w-3" /> Date Range / Period
                  </label>
                  <select
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 outline-none"
                  >
                    <option value="">All Periods (Full Historical Dataset)</option>
                    <option value="this_month">Current Month</option>
                    <option value="this_quarter">Current Quarter</option>
                    <option value="this_year">Current Year</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-600 flex items-center gap-1">
                    <Filter className="h-3 w-3" /> Segment Filter
                  </label>
                  <input
                    type="text"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    placeholder="e.g. Technology, North, HR..."
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 outline-none"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-100 bg-slate-50/70 px-6 py-4 flex items-center justify-end gap-3">
          <Button variant="secondary" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleRunGenerate}
            disabled={submitting || loadingTypes || !selectedType}
            className="bg-brand-600 hover:bg-brand-700 text-white font-bold"
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Computing Analytics...
              </>
            ) : (
              <>
                <Sparkles className="mr-1.5 h-4 w-4" />
                Generate Report
              </>
            )}
          </Button>
        </div>
      </Card>
    </div>
  )
}
