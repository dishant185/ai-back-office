import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  Database,
  Eye,
  FileText,
  GitFork,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  Zap,
} from 'lucide-react'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { CardSkeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorBoundary } from '../components/ui/ErrorBoundary'
import { PageHeader } from '../components/ui/PageHeader'
import type { MappingSuggestion, MappingValidationResult, StandardizedDataset } from '../types/mapping'
import api from '../services/api'

const defaultFieldCatalog = [
  // HR / Talent
  { key: 'employee_id', label: 'Employee ID', category: 'HR / Talent', description: 'Unique identifier for employee record' },
  { key: 'employee_name', label: 'Employee Name', category: 'HR / Talent', description: 'Full employee legal or preferred name' },
  { key: 'age', label: 'Employee Age', category: 'HR / Talent', description: 'Age in completed years' },
  { key: 'attrition', label: 'Attrition Status', category: 'HR / Talent', description: 'Departure or flight indicator (Yes/No, 1/0)' },
  { key: 'department', label: 'Department / Unit', category: 'HR / Talent', description: 'Business functional department' },
  { key: 'job_role', label: 'Job Role / Title', category: 'HR / Talent', description: 'Designation or functional title' },
  { key: 'monthly_income', label: 'Monthly Compensation', category: 'HR / Talent', description: 'Base monthly salary or income' },
  { key: 'years_at_company', label: 'Tenure (Years at Org)', category: 'HR / Talent', description: 'Total continuous employment tenure' },
  { key: 'education', label: 'Education Level', category: 'HR / Talent', description: 'Highest qualification degree' },
  { key: 'gender', label: 'Gender Demographics', category: 'HR / Talent', description: 'Gender identification' },
  { key: 'work_life_balance', label: 'Work Life Rating', category: 'HR / Talent', description: 'Satisfaction index (1 to 5)' },

  // Commercial / Sales
  { key: 'customer_name', label: 'Customer / Client Name', category: 'Commercial / Sales', description: 'Client or purchasing account' },
  { key: 'dealer_name', label: 'Channel Partner / Dealer', category: 'Commercial / Sales', description: 'Sales distribution partner' },
  { key: 'region', label: 'Geographic Region', category: 'Commercial / Sales', description: 'Sales territory or operational geography' },
  { key: 'transaction_date', label: 'Transaction Date', category: 'Commercial / Sales', description: 'Timestamp of business event' },
  { key: 'product', label: 'Product / SKU', category: 'Commercial / Sales', description: 'Commercial product item' },
  { key: 'quantity', label: 'Order Volume / Units', category: 'Commercial / Sales', description: 'Quantity sold or delivered' },
  { key: 'revenue', label: 'Gross Revenue ($)', category: 'Commercial / Sales', description: 'Top-line sales amount' },
  { key: 'cost', label: 'Cost of Goods Sold ($)', category: 'Commercial / Sales', description: 'Direct or indirect costs' },
  { key: 'profit', label: 'Operating Profit ($)', category: 'Commercial / Sales', description: 'Gross or net margin' },
  { key: 'target', label: 'Quota / Budget Target', category: 'Commercial / Sales', description: 'Commercial plan benchmark' },
]

interface MappingRowState {
  source: string
  target: string
  ignored: boolean
  confidence: number
  status: string
  reason: string
  normalized: string
}

interface MappingListItem {
  upload_id: string
  filename: string
  file_size: number
  row_count: number
  column_count: number
  mapped_fields: number
  unmapped_fields: number
  total_fields: number
  updated_at: string
}

function readWorkflowIntent(): 'report_generation' | null {
  try {
    const raw = sessionStorage.getItem('ai_backoffice_workflow')
    if (!raw) return null
    const parsed = JSON.parse(raw) as { intent?: string }
    return parsed.intent === 'report_generation' ? 'report_generation' : null
  } catch {
    return null
  }
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'Recently'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return 'Recently'
    return d.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return 'Recently'
  }
}


export default function MappingPage() {
  const navigate = useNavigate()
  const { uploadId: routeUploadId } = useParams()

  // ── List mode state ──
  const [mappingsList, setMappingsList] = useState<MappingListItem[]>([])
  const [listLoading, setListLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<MappingListItem | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  // ── Editor mode state ──
  const [rows, setRows] = useState<MappingRowState[]>([])
  const [loading, setLoading] = useState(false)
  const [validationMessage, setValidationMessage] = useState('')
  const [validationStatus, setValidationStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [standardizedData, setStandardizedData] = useState<StandardizedDataset | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)
  const [uploadId, setUploadId] = useState<string | null>(routeUploadId ?? null)
  const [isApplying, setIsApplying] = useState(false)
  const [activeFilter, setActiveFilter] = useState<'all' | 'mapped' | 'review' | 'ignored'>('all')
  const [editorSearchQuery, setEditorSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'mapping' | 'preview'>('mapping')
  const [editorMode, setEditorMode] = useState(false)
  const [fieldCatalog, setFieldCatalog] = useState(defaultFieldCatalog)

  useEffect(() => {
    api.get<Array<{ key: string; label: string; category?: string; description?: string }>>('/api/v1/mappings/catalog')
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length > 0) {
          setFieldCatalog(
            res.data.map((f) => ({
              key: f.key,
              label: f.label || f.key,
              category: f.category ? f.category.toUpperCase() : 'UNIVERSAL',
              description: f.description || 'Harmonized field',
            }))
          )
        }
      })
      .catch(() => {
        // Fallback to default catalog
      })
  }, [])

  const summary = useMemo(() => {
    const mapped = rows.filter((row) => row.target && !row.ignored).length
    const needsReview = rows.filter((row) => (!row.target || row.status === 'needs_review') && !row.ignored).length
    const unmapped = rows.filter((row) => !row.target && !row.ignored).length
    const ignored = rows.filter((row) => row.ignored).length
    return { mapped, needsReview, unmapped, ignored, total: rows.length }
  }, [rows])

  // ── Fetch saved mappings list ──
  const fetchMappingsList = async () => {
    try {
      setListLoading(true)
      const response = await api.get<MappingListItem[]>('/api/v1/mappings/list')
      setMappingsList(response.data)
    } catch {
      setMappingsList([])
    } finally {
      setListLoading(false)
    }
  }

  // ── Delete dataset handler ──
  const handleDeleteDataset = async () => {
    if (!deleteTarget) return
    try {
      setIsDeleting(true)
      setDeleteError(null)
      await api.delete(`/api/v1/datasets/${deleteTarget.upload_id}`)
      setDeleteTarget(null)
      await fetchMappingsList()
    } catch (err: any) {
      setDeleteError(err?.response?.data?.detail || 'Failed to delete dataset')
    } finally {
      setIsDeleting(false)
    }
  }

  // ── Enter editor mode ──
  const enterEditor = (targetUploadId: string) => {
    setUploadId(targetUploadId)
    setEditorMode(true)
    setLoading(true)
    navigate(`/mapping/${targetUploadId}`, { replace: true })
  }

  const handleBackToList = () => {
    setEditorMode(false)
    setUploadId(null)
    setRows([])
    setStandardizedData(null)
    setValidationMessage('')
    setValidationStatus('idle')
    setActiveTab('mapping')
    navigate('/mapping', { replace: true })
  }

  // ── Initial load ──
  useEffect(() => {
    if (routeUploadId) {
      // Direct link to a mapping editor
      setUploadId(routeUploadId)
      setEditorMode(true)
    } else {
      // When navigating to /mapping, show all mapping cards
      setUploadId(null)
      setEditorMode(false)
    }

    void fetchMappingsList()
  }, [routeUploadId])

  // ── Auto-generate or fetch standardized preview ──
  const loadStandardizedPreview = async (targetUploadId?: string, targetRows?: MappingRowState[]) => {
    const id = targetUploadId || uploadId
    const activeRows = targetRows || rows
    if (!id || !activeRows.length) return

    setIsPreviewLoading(true)
    try {
      const payload = {
        mappings: activeRows.map((row) => ({
          source: row.source,
          target: row.target || undefined,
          ignored: row.ignored,
          confidence: row.confidence,
          status: row.status,
          reason: row.reason,
          method: 'manual',
          user_confirmed: Boolean(row.target),
        })),
        upload_id: id,
      }

      const response = await api.post<{
        success: boolean
        row_count?: number
        column_count?: number
        columns?: string[]
        preview?: Array<Record<string, unknown>>
        standardized?: {
          rows: Array<Record<string, unknown>>
          columns: string[]
        }
      }>('/api/v1/mappings/apply', payload)

      if (response.data.success) {
        const standardized = response.data.standardized ?? {
          rows: response.data.preview ?? [],
          columns: response.data.columns ?? [],
        }

        const nextStandardized: StandardizedDataset = {
          success: true,
          rows: standardized.rows,
          columns: standardized.columns,
          row_count: response.data.row_count ?? standardized.rows.length,
          column_count: response.data.column_count ?? standardized.columns.length,
        }

        setStandardizedData(nextStandardized)
      }
    } catch (err) {
      console.warn('Preview generation error:', err)
    } finally {
      setIsPreviewLoading(false)
    }
  }

  // ── Load mapping suggestions when editor opens ──
  useEffect(() => {
    if (!editorMode || !uploadId) return

    const loadData = async () => {
      try {
        setLoading(true)
        setValidationMessage('')
        setValidationStatus('idle')

        let columns: string[] = []

        // 1. Fetch column schema for this specific dataset
        try {
          const schemaResp = await api.get(`/api/v1/datasets/${uploadId}/schema`)
          if (schemaResp.data?.columns && Array.isArray(schemaResp.data.columns)) {
            columns = schemaResp.data.columns.map((c: any) => c.original_name || c.name)
          }
        } catch {
          // fallback
        }

        // 2. Fallback to session storage if applicable
        if (!columns.length) {
          const stored = sessionStorage.getItem('ai_backoffice_latest_upload')
          const storedPayload = stored ? (JSON.parse(stored) as { dataset?: { preview?: Array<Record<string, unknown>> } }) : null
          if (storedPayload?.dataset?.preview && storedPayload.dataset.preview.length > 0) {
            columns = Object.keys(storedPayload.dataset.preview[0])
          }
        }

        if (!columns.length) {
          setValidationStatus('error')
          setValidationMessage('Unable to detect dataset dimensions. Please re-upload your file.')
          setLoading(false)
          return
        }

        // 3. Check for existing saved mappings for this dataset
        let savedMappings: Array<{ source: string; target: string; ignored?: boolean; confidence?: number; status?: string; reason?: string }> = []
        try {
          const savedResp = await api.get(`/api/v1/mappings/${uploadId}`)
          if (savedResp.data?.mappings && Array.isArray(savedResp.data.mappings) && savedResp.data.mappings.length > 0) {
            savedMappings = savedResp.data.mappings
          }
        } catch {
          // proceed with fresh suggestions
        }

        // 4. Request mapping suggestions
        const response = await api.post<{ success: boolean; columns: MappingSuggestion[] }>(
          '/api/v1/mappings/suggest',
          { columns, dataset_id: uploadId },
        )

        if (!response.data.success || !Array.isArray(response.data.columns)) {
          throw new Error('No mapping suggestions returned.')
        }

        const savedMap = new Map(savedMappings.map((m) => [m.source, m]))
        const nextRows = response.data.columns.map((item) => {
          const saved = savedMap.get(item.source)
          return {
            source: item.source,
            target: saved ? saved.target : (item.suggested_target ?? ''),
            ignored: saved ? Boolean(saved.ignored) : false,
            confidence: saved?.confidence ? Number(saved.confidence) : Number(item.confidence ?? 0),
            status: saved?.status ?? (item.status ?? 'needs_review'),
            reason: saved?.reason ?? (item.reason ?? 'Automated recommendation'),
            normalized: item.normalized ?? item.source,
          }
        })

        setRows(nextRows)
        setLoading(false)
        void loadStandardizedPreview(uploadId, nextRows)
      } catch (requestError: any) {
        setValidationStatus('error')
        setValidationMessage(requestError?.message || 'Unable to generate column mappings.')
        setLoading(false)
      }
    }

    void loadData()
  }, [editorMode, uploadId])

  const handleTargetChange = (source: string, target: string) => {
    setRows((current) =>
      current.map((row) =>
        row.source === source
          ? {
              ...row,
              target,
              ignored: false,
              status: target ? 'suggested' : 'needs_review',
              confidence: target ? Math.max(row.confidence || 85, 85) : 0,
              reason: target ? 'User selected mapping' : 'Needs review',
            }
          : row,
      ),
    )
  }

  const handleIgnore = (source: string) => {
    setRows((current) =>
      current.map((row) =>
        row.source === source
          ? {
              ...row,
              ignored: !row.ignored,
              target: row.ignored ? row.target : '',
              status: row.ignored ? 'suggested' : 'ignored',
              reason: row.ignored ? 'User selected mapping' : 'Ignored by user',
            }
          : row,
      ),
    )
  }

  const handleValidate = async () => {
    if (!uploadId) return

    try {
      const payload = {
        mappings: rows.map((row) => ({
          source: row.source,
          target: row.target || undefined,
          ignored: row.ignored,
          confidence: row.confidence,
          status: row.status,
          reason: row.reason,
          method: 'manual',
          user_confirmed: Boolean(row.target),
        })),
      }

      const response = await api.post<{ success: boolean; validation: MappingValidationResult }>(
        '/api/v1/mappings/validate',
        payload,
      )

      const result = response.data.validation
      if (response.data.success && result.valid) {
        setValidationStatus('success')
        setValidationMessage('✓ Mapping verification passed. Schema is harmonized with 0 conflicts.')
        return
      }

      setValidationStatus('error')
      setValidationMessage(result.errors[0] ?? 'Mapping validation detected schema conflicts.')
    } catch {
      setValidationStatus('error')
      setValidationMessage('Mapping validation failed. Please check for conflicting fields.')
    }
  }

  const handleApply = async () => {
    if (!uploadId) return

    setIsApplying(true)
    setValidationStatus('idle')
    setValidationMessage('')

    try {
      const payload = {
        mappings: rows.map((row) => ({
          source: row.source,
          target: row.target || undefined,
          ignored: row.ignored,
          confidence: row.confidence,
          status: row.status,
          reason: row.reason,
          method: 'manual',
          user_confirmed: Boolean(row.target),
        })),
      }

      const response = await api.post<{
        success: boolean
        row_count?: number
        column_count?: number
        columns?: string[]
        preview?: Array<Record<string, unknown>>
        standardized?: {
          rows: Array<Record<string, unknown>>
          columns: string[]
        }
      }>('/api/v1/mappings/apply', {
        ...payload,
        upload_id: uploadId,
      })

      if (!response.data.success) {
        setValidationStatus('error')
        setValidationMessage('Unable to apply canonical mapping.')
        return
      }

      const standardized = response.data.standardized ?? {
        rows: response.data.preview ?? [],
        columns: response.data.columns ?? [],
      }

      const nextStandardized = {
        success: true,
        rows: standardized.rows,
        columns: standardized.columns,
        row_count: response.data.row_count ?? standardized.rows.length,
        column_count: response.data.column_count ?? standardized.columns.length,
      }

      setStandardizedData(nextStandardized)
      setActiveTab('preview')
      setValidationStatus('success')
      setValidationMessage(`✓ Harmonization complete. ${nextStandardized.row_count} records standardized across ${nextStandardized.column_count} fields.`)

      sessionStorage.setItem('ai_backoffice_mappings', JSON.stringify(payload.mappings))

      // Refresh list in background
      void fetchMappingsList()

      if (readWorkflowIntent() === 'report_generation') {
        sessionStorage.setItem('ai_backoffice_workflow', JSON.stringify({ intent: 'report_generation' }))
        navigate(`/reports?datasetId=${uploadId}`)
        return
      }
    } catch {
      setValidationStatus('error')
      setValidationMessage('Unable to standardize dataset. Please check your mappings.')
    } finally {
      setIsApplying(false)
    }
  }

  // Filter rows for editor
  const filteredRows = rows.filter((r) => {
    const matchesSearch =
      r.source.toLowerCase().includes(editorSearchQuery.toLowerCase()) ||
      r.target.toLowerCase().includes(editorSearchQuery.toLowerCase()) ||
      r.reason.toLowerCase().includes(editorSearchQuery.toLowerCase())

    if (!matchesSearch) return false

    if (activeFilter === 'mapped') return r.target && !r.ignored
    if (activeFilter === 'review') return (!r.target || r.status === 'needs_review') && !r.ignored
    if (activeFilter === 'ignored') return r.ignored
    return true
  })

  // Filter list by search
  const filteredMappings = mappingsList.filter((m) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      m.filename?.toLowerCase().includes(q) ||
      m.upload_id?.toLowerCase().includes(q)
    )
  })

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ► EDITOR MODE — Column mapping editor
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  if (editorMode) {
    if (loading) {
      return (
        <div className="space-y-8 animate-fade-in">
          <PageHeader
            eyebrow="Schema Harmonization"
            title="Column Mapping Studio"
            description="Automating column role matching and canonical entity linking..."
            actions={
              <Button variant="secondary" size="sm" onClick={handleBackToList}>
                <ChevronLeft className="mr-1.5 h-3.5 w-3.5" />
                All Mappings
              </Button>
            }
          />
          <Card className="border-slate-200">
            <CardContent className="py-20 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 animate-spin">
                <RefreshCw className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Harmonizing Column Schemas...</h3>
              <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
                Running semantic keyword proximity, token similarity, and domain role mapping against canonical enterprise ontology.
              </p>
            </CardContent>
          </Card>
        </div>
      )
    }

    return (
      <div className="space-y-8 animate-fade-in pb-12">
        {/* Top Header */}
        <PageHeader
          eyebrow="Schema Harmonization Studio"
          title="Canonical Column Mapping"
          description="Verify and calibrate how raw spreadsheet columns map to enterprise analytics parameters."
          actions={
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={handleBackToList}>
                <ChevronLeft className="mr-1.5 h-3.5 w-3.5" />
                All Mappings
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleApply}
                disabled={isApplying}
                className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25"
              >
                {isApplying ? (
                  <>
                    <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    Harmonizing...
                  </>
                ) : (
                  <>
                    <Zap className="mr-1.5 h-4 w-4" />
                    Apply &amp; Standardize
                  </>
                )}
              </Button>
            </div>
          }
        />

        {/* Hero Banner */}
        <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl shadow-slate-900/10">
          <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
          <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-indigo-500/15 blur-3xl" />

          <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="space-y-2 max-w-xl">
              <div className="flex items-center gap-2">
                <Badge variant="brand" className="bg-brand-500/20 text-brand-300 border-brand-400/30 text-xs">
                  Deterministic Matcher v2.4
                </Badge>
                <Badge variant="success" className="bg-emerald-500/20 text-emerald-300 border-emerald-400/30 text-xs">
                  Zero Data Loss
                </Badge>
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                Schema Harmonization &amp; Entity Normalization
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Mapped fields feed directly into the Universal Intelligence Engine to generate department metrics,
                distribution charts, and anomaly diagnostics.
              </p>
            </div>

            <div className="flex flex-col sm:items-end gap-2 w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-white/10">
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span>100% Conflict Free</span>
              </div>
              <p className="text-xs text-slate-400 font-mono">ID: {uploadId?.slice(0, 24)}...</p>
            </div>
          </div>

          {/* 4 Telemetry tiles */}
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-white/10 pt-6">
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Fields</p>
              <p className="text-xl font-bold text-white mt-0.5">{summary.total}</p>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Harmonized</p>
              <p className="text-xl font-bold text-emerald-400 mt-0.5">{summary.mapped}</p>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-400">Needs Review</p>
              <p className="text-xl font-bold text-amber-300 mt-0.5">{summary.needsReview}</p>
            </div>
            <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Excluded</p>
              <p className="text-xl font-bold text-slate-400 mt-0.5">{summary.ignored}</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab('mapping')}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition ${
                activeTab === 'mapping'
                  ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <GitFork className="h-4 w-4" />
              Column Matcher ({rows.length})
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab('preview')
                if (!standardizedData && !isPreviewLoading) {
                  void loadStandardizedPreview()
                }
              }}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition ${
                activeTab === 'preview'
                  ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Eye className="h-4 w-4" />
              Standardized Output Preview {standardizedData ? `(${standardizedData.row_count} rows)` : ''}
              {isPreviewLoading && <Loader2 className="h-3 w-3 animate-spin text-brand-600 ml-1" />}
            </button>
          </div>

          {activeTab === 'mapping' && (
            <Button variant="ghost" size="sm" onClick={handleValidate} className="text-xs">
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5 text-brand-600" />
              Validate Rules
            </Button>
          )}
        </div>

        {/* Validation banner */}
        {validationMessage && (
          <div
            className={`flex items-start gap-3 rounded-2xl p-4 text-xs font-semibold animate-slide-up border ${
              validationStatus === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-red-50 border-red-200 text-red-900'
            }`}
          >
            {validationStatus === 'success' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">{validationMessage}</div>
          </div>
        )}

        {/* Tab Content 1: Column Matcher */}
        {activeTab === 'mapping' && (
          <Card className="border-slate-200/80 shadow-sm overflow-hidden">
            {/* Filter & Search Bar */}
            <div className="border-b border-slate-100 bg-slate-50/60 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-1.5">
                {[
                  { id: 'all', label: `All Fields (${rows.length})` },
                  { id: 'mapped', label: `Harmonized (${summary.mapped})` },
                  { id: 'review', label: `Needs Review (${summary.needsReview})` },
                  { id: 'ignored', label: `Excluded (${summary.ignored})` },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveFilter(tab.id as any)}
                    className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                      activeFilter === tab.id
                        ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                        : 'text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={editorSearchQuery}
                  onChange={(e) => setEditorSearchQuery(e.target.value)}
                  placeholder="Search columns..."
                  className="w-full rounded-xl border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-700 shadow-2xs outline-none focus:border-brand-400"
                />
              </div>
            </div>

            {/* Table Header */}
            <div className="hidden md:grid grid-cols-[1.4fr_1.8fr_1fr_0.8fr] gap-4 px-6 py-3 border-b border-slate-100 bg-slate-100/50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              <div>Source Spreadsheet Column</div>
              <div>Target Canonical Entity</div>
              <div>Confidence &amp; Reasoning</div>
              <div className="text-right">Action</div>
            </div>

            {/* Rows List */}
            <div className="divide-y divide-slate-100">
              {filteredRows.map((row) => {
                const isConfident = row.confidence >= 80
                return (
                  <div
                    key={row.source}
                    className={`grid gap-4 p-5 md:grid-cols-[1.4fr_1.8fr_1fr_0.8fr] md:items-center transition ${
                      row.ignored
                        ? 'bg-slate-50/40 opacity-60'
                        : 'hover:bg-brand-50/20'
                    }`}
                  >
                    {/* Source Column */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900">{row.source}</span>
                        {row.ignored && (
                          <span className="rounded-md bg-slate-200 px-1.5 py-0.5 text-[10px] font-bold text-slate-600">
                            IGNORED
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 font-mono truncate">{row.normalized}</p>
                    </div>

                    {/* Target Select */}
                    <div>
                      <select
                        value={row.target}
                        disabled={row.ignored}
                        onChange={(e) => handleTargetChange(row.source, e.target.value)}
                        className={`w-full rounded-xl border px-3.5 py-2 text-xs font-semibold shadow-2xs outline-none transition ${
                          row.target
                            ? 'border-brand-200 bg-white text-slate-900 focus:border-brand-500'
                            : 'border-amber-200 bg-amber-50/40 text-amber-900 focus:border-amber-400'
                        }`}
                      >
                        <option value="">— Select Canonical Parameter —</option>
                        {fieldCatalog.map((fc) => (
                          <option key={fc.key} value={fc.key}>
                            [{fc.category}] {fc.label}
                          </option>
                        ))}
                      </select>
                      {row.target && (
                        <p className="mt-1 text-[10px] text-slate-500 truncate">
                          {fieldCatalog.find((f) => f.key === row.target)?.description || 'Harmonized field'}
                        </p>
                      )}
                    </div>

                    {/* Confidence */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-700">{row.confidence}% match</span>
                        {isConfident ? (
                          <Badge variant="success" className="text-[10px] px-1.5 py-0">High</Badge>
                        ) : row.confidence > 0 ? (
                          <Badge variant="warning" className="text-[10px] px-1.5 py-0">Review</Badge>
                        ) : (
                          <Badge variant="default" className="text-[10px] px-1.5 py-0">Unset</Badge>
                        )}
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isConfident
                              ? 'bg-emerald-500'
                              : row.confidence > 40
                              ? 'bg-amber-400'
                              : 'bg-slate-300'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, row.confidence))}%` }}
                        />
                      </div>
                      <p className="text-[10px] text-slate-400 truncate">{row.reason}</p>
                    </div>

                    {/* Action */}
                    <div className="flex items-center justify-end">
                      <button
                        type="button"
                        onClick={() => handleIgnore(row.source)}
                        className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                          row.ignored
                            ? 'border border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200'
                            : 'border border-slate-200 bg-white text-slate-500 hover:border-red-200 hover:bg-red-50 hover:text-red-600'
                        }`}
                      >
                        {row.ignored ? 'Include' : 'Exclude'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Bottom Action Footer */}
            <div className="border-t border-slate-100 bg-slate-50/60 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-500">
                <span className="font-bold text-slate-800">{summary.mapped} of {summary.total} fields</span> verified for canonical analysis.
              </div>
              <div className="flex items-center gap-3">
                <Button variant="secondary" size="sm" onClick={handleBackToList}>
                  Back to Mappings
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleApply}
                  disabled={isApplying}
                  className="bg-brand-600 hover:bg-brand-700 text-white font-bold"
                >
                  {isApplying ? 'Harmonizing...' : 'Apply & Standardize Dataset'}
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Tab Content 2: Standardized Preview */}
        {activeTab === 'preview' && (
          isPreviewLoading && !standardizedData ? (
            <Card className="border-slate-200/80 shadow-sm p-12 text-center bg-white">
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Generating Standardized Output Preview...</h3>
                  <p className="text-xs text-slate-500 mt-1">Applying schema harmonization rules across dataset records.</p>
                </div>
              </div>
            </Card>
          ) : standardizedData ? (
            <Card className="border-slate-200/80 shadow-sm overflow-hidden bg-white">
              <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-slate-100 bg-slate-50/50">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-slate-900">Standardized Schema Output</h2>
                    <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-200">
                      Harmonized Preview
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {standardizedData.row_count} records standardized across {standardizedData.column_count} canonical fields.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void loadStandardizedPreview()}
                    disabled={isPreviewLoading}
                    className="text-xs"
                  >
                    <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isPreviewLoading ? 'animate-spin' : ''}`} />
                    Refresh Preview
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => navigate(`/reports?datasetId=${uploadId}`)}
                    className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25 text-xs"
                  >
                    <FileText className="mr-1.5 h-4 w-4" />
                    Generate Executive Report
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-100/70">
                        <th className="px-4 py-3 font-bold uppercase tracking-wider text-slate-500">#</th>
                        {standardizedData.columns.map((col) => (
                          <th key={col} className="px-4 py-3 font-bold uppercase tracking-wider text-slate-700 whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {standardizedData.rows.slice(0, 10).map((row, idx) => (
                        <tr key={idx} className="border-b border-slate-100 odd:bg-white even:bg-slate-50/50 hover:bg-brand-50/30 transition">
                          <td className="px-4 py-2.5 text-slate-400 font-mono">{idx + 1}</td>
                          {standardizedData.columns.map((col) => (
                            <td key={col} className="px-4 py-2.5 text-slate-700 whitespace-nowrap">
                              {String(row[col] ?? '—')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="border-t border-slate-100 p-4 bg-slate-50/60 flex items-center justify-between">
                  <span className="text-xs text-slate-500">Showing first 10 rows for verification</span>
                  <div className="flex items-center gap-3">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setActiveTab('mapping')}
                    >
                      <ChevronLeft className="mr-1.5 h-4 w-4" />
                      Back to Column Matcher
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => navigate(`/reports?datasetId=${uploadId}`)}
                      className="bg-brand-600 hover:bg-brand-700 text-white font-bold"
                    >
                      Generate Executive Report
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-slate-200/80 shadow-sm p-12 text-center bg-white">
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600">
                  <AlertCircle className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Standardized Preview Not Ready</h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm">
                    Harmonize and preview your dataset records using the configured column rules.
                  </p>
                </div>
                <Button
                  size="sm"
                  onClick={() => void loadStandardizedPreview()}
                  className="bg-brand-600 hover:bg-brand-700 text-white font-bold mt-2"
                >
                  <Eye className="mr-1.5 h-4 w-4" />
                  Generate Preview Now
                </Button>
              </div>
            </Card>
          )
        )}
      </div>
    )
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ► LIST VIEW — Browse all saved mappings
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  return (
    <ErrorBoundary fallbackTitle="Column Mapping Studio">
      <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Header */}
      <PageHeader
        eyebrow="Schema Harmonization Studio"
        title="Column Mapping Library"
        description="Browse and manage all dataset column mappings. Click a mapping to open the editor."
        actions={
          <Button
            variant="default"
            size="sm"
            onClick={() => navigate('/upload')}
            className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25"
          >
            <Plus className="mr-1.5 h-4 w-4" />
            Map New Dataset
          </Button>
        }
      />

      {/* Hero Stats Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl shadow-slate-900/10">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-indigo-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-brand-500/15 blur-3xl" />

        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1 rounded-full border border-brand-400/30 bg-brand-500/20 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider text-brand-300">
                <GitFork className="h-3 w-3" />
                Schema Library
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Mapping Configuration Archive
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              All previously harmonized dataset schemas — click to review, edit, or re-apply.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 w-full sm:w-auto">
            <div className="rounded-xl bg-white/5 backdrop-blur-sm p-3 min-w-[100px]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-brand-300">Total Mappings</p>
              <p className="text-2xl font-black text-white mt-0.5">{mappingsList.length}</p>
            </div>
            <div className="rounded-xl bg-white/5 backdrop-blur-sm p-3 min-w-[100px]">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-300">Datasets</p>
              <p className="text-2xl font-black text-emerald-400 mt-0.5">
                {new Set(mappingsList.map(m => m.upload_id)).size}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      {mappingsList.length > 0 && (
        <div className="relative">
          <Search className="absolute left-4 top-3.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search mappings by filename or dataset ID..."
            className="w-full rounded-2xl border border-slate-200 bg-white pl-11 pr-4 py-3 text-sm text-slate-700 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          />
        </div>
      )}

      {/* Loading state */}
      {listLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <CardSkeleton key={i} lines={3} />
          ))}
        </div>
      )}

      {/* Mapping Cards Grid */}
      {!listLoading && filteredMappings.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredMappings.map((m) => {
            const mappedPct = m.total_fields > 0 ? Math.round((m.mapped_fields / m.total_fields) * 100) : 0
            return (
              <button
                key={m.upload_id}
                type="button"
                onClick={() => enterEditor(m.upload_id)}
                className="group relative text-left overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:border-brand-300 hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-brand-400"
              >
                {/* Decorative gradient */}
                <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-indigo-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100 blur-2xl" />

                <div className="relative z-10 space-y-4">
                  {/* Icon + badge + delete action */}
                  <div className="flex items-center justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition-transform duration-200 group-hover:scale-110">
                      <GitFork className="h-5 w-5" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
                        mappedPct >= 80
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                          : mappedPct >= 50
                            ? 'border-amber-200 bg-amber-50 text-amber-700'
                            : 'border-slate-200 bg-slate-50 text-slate-600'
                      }`}>
                        {mappedPct}% Mapped
                      </span>
                      <button
                        type="button"
                        title="Delete dataset"
                        onClick={(e) => {
                          e.stopPropagation()
                          setDeleteTarget(m)
                        }}
                        className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Filename */}
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 line-clamp-1 group-hover:text-brand-700 transition-colors">
                      {m.filename || 'Unnamed Dataset'}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono truncate">
                      {m.upload_id}
                    </p>
                  </div>

                  {/* Stats row */}
                  <div className="flex flex-wrap items-center gap-2 text-[11px]">
                    <span className="flex items-center gap-1 text-slate-500">
                      <Layers className="h-3 w-3" />
                      {m.mapped_fields}/{m.total_fields} fields
                    </span>
                    <span className="h-3 w-px bg-slate-200" />
                    <span className="flex items-center gap-1 text-slate-500">
                      <Database className="h-3 w-3" />
                      {(m.row_count ?? 0).toLocaleString()} rows
                    </span>
                    <span className="h-3 w-px bg-slate-200" />
                    <span className="flex items-center gap-1 text-slate-500">
                      <Calendar className="h-3 w-3" />
                      {formatDate(m.updated_at)}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        mappedPct >= 80 ? 'bg-emerald-500' : mappedPct >= 50 ? 'bg-amber-400' : 'bg-slate-300'
                      }`}
                      style={{ width: `${mappedPct}%` }}
                    />
                  </div>
                </div>

                {/* Hover arrow */}
                <div className="absolute right-4 bottom-4 opacity-0 translate-x-2 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <ChevronLeft className="h-4 w-4 rotate-180" />
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* Empty State */}
      {!listLoading && mappingsList.length === 0 && (
        <EmptyState
          icon={GitFork}
          title="No Column Mappings Yet"
          description="Upload a CSV or Excel dataset first, then configure column mappings to harmonize your data for deterministic intelligence reporting."
          actionLabel="Upload Dataset to Map"
          onAction={() => navigate('/upload')}
        />
      )}

      {/* No search results */}
      {!listLoading && mappingsList.length > 0 && filteredMappings.length === 0 && searchQuery && (
        <EmptyState
          icon={Search}
          title="No Mappings Found"
          description={`No column mappings matched "${searchQuery}". Try a different search term or clear the filter.`}
          actionLabel="Clear Search"
          onAction={() => setSearchQuery('')}
        />
      )}
      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center gap-3 text-red-600">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50">
                <Trash2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Delete Dataset</h3>
                <p className="text-xs text-slate-500">This action cannot be undone.</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              Are you sure you want to delete <strong className="text-slate-900">{deleteTarget.filename || deleteTarget.upload_id}</strong>? All mapped dimensions, cached profiles, and associated intelligence will be permanently removed.
            </p>
            {deleteError && (
              <div className="p-2.5 rounded-lg bg-red-50 text-red-700 text-xs font-medium">
                {deleteError}
              </div>
            )}
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={isDeleting}
                onClick={() => { setDeleteTarget(null); setDeleteError(null); }}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                size="sm"
                disabled={isDeleting}
                onClick={handleDeleteDataset}
                className="bg-red-600 hover:bg-red-700 text-white font-bold"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                    Delete Dataset
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}
