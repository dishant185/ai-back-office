import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Loader2,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
  Zap,
} from 'lucide-react'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { StatCard } from '../components/ui/StatCard'
import api from '../services/api'
import type { DatasetSummary, UploadResult } from '../types/mapping'

const MAX_FILE_SIZE_MB = 25

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 Bytes'
  const units = ['Bytes', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** index
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`
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

export default function UploadPage() {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadState, setUploadState] = useState<
    'idle' | 'selected' | 'uploading' | 'success' | 'error'
  >('idle')
  const [error, setError] = useState('')
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null)
  const [uploadId, setUploadId] = useState<string | null>(null)

  const handleFileSelection = (file: File | null) => {
    if (!file) return

    const allowedTypes = ['csv', 'xlsx', 'xls']
    const extension = file.name.split('.').pop()?.toLowerCase() ?? ''

    if (!allowedTypes.includes(extension)) {
      setError('Unsupported file format. Please upload an enterprise CSV or Excel (.xlsx/.xls) workbook.')
      setUploadState('error')
      return
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File volume exceeds limit. Maximum allowed size is ${MAX_FILE_SIZE_MB} MB.`)
      setUploadState('error')
      return
    }

    setSelectedFile(file)
    setError('')
    setUploadState('selected')
  }

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFileSelection(event.target.files?.[0] ?? null)
  }

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    handleFileSelection(event.dataTransfer.files?.[0] ?? null)
  }

  useEffect(() => {
    const intent = new URLSearchParams(location.search).get('intent')
    if (intent === 'report_generation') {
      sessionStorage.setItem('ai_backoffice_workflow', JSON.stringify({ intent: 'report_generation' }))
    }
  }, [location.search])

  const resetUpload = () => {
    setSelectedFile(null)
    setError('')
    setUploadState('idle')
    setDatasetSummary(null)
    setUploadId(null)
    sessionStorage.removeItem('ai_backoffice_latest_upload')
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadState('uploading')
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await api.post<UploadResult>('/api/v1/uploads', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      const result = response.data
      setUploadId(result.upload_id)
      setDatasetSummary(result.dataset ?? null)
      sessionStorage.setItem(
        'ai_backoffice_latest_upload',
        JSON.stringify({
          uploadId: result.upload_id,
          dataset: result.dataset,
          fileName: selectedFile?.name || 'dataset.csv',
        }),
      )
      setUploadState('success')

      if (readWorkflowIntent() === 'report_generation') {
        navigate(`/mapping/${result.upload_id}`)
        return
      }
    } catch (uploadError: any) {
      const message =
        uploadError?.response?.data?.detail ||
        uploadError?.message ||
        'Unable to process uploaded dataset.'
      setError(message)
      setUploadState('error')
    }
  }

  // Quick helper to load pre-built demo file
  const loadDemoData = () => {
    const csvContent = `EmpID,Age,Attrition,Department,DistanceFromHome,Education,JobRole,MonthlyIncome,YearsAtCompany,WorkLifeBalance
E1001,41,Yes,Sales,1,2,Sales Executive,5993,6,1
E1002,49,No,Research & Development,8,1,Research Scientist,5130,10,3
E1003,37,Yes,Research & Development,2,2,Laboratory Technician,2090,0,3
E1004,33,No,Research & Development,3,4,Research Scientist,2909,8,3
E1005,27,No,Research & Development,2,1,Laboratory Technician,3468,2,3
E1006,32,No,Research & Development,2,2,Laboratory Technician,3068,7,2
E1007,59,No,Research & Development,16,3,Laboratory Technician,2670,1,2
E1008,30,No,Research & Development,24,1,Laboratory Technician,2693,1,3
E1009,38,No,Research & Development,23,3,Manufacturing Director,9526,9,3
E1010,36,No,Research & Development,27,3,Healthcare Representative,5237,7,2`
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const file = new File([blob], 'Enterprise_HR_Talent_Sample.csv', { type: 'text/csv' })
    handleFileSelection(file)
  }

  const progressWidth =
    uploadState === 'success' ? '100%' : uploadState === 'uploading' ? '70%' : '35%'

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Header */}
      <PageHeader
        eyebrow="Data Ingestion & Profiling"
        title="Enterprise Dataset Ingestion"
        description="Upload raw CSV or Excel spreadsheets for automatic schema profiling, statistical hygiene audit, and domain role detection."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={loadDemoData} title="Load pre-configured sample data">
              <Sparkles className="mr-1.5 h-3.5 w-3.5 text-brand-600" />
              Try Sample Dataset
            </Button>
          </div>
        }
      />

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl shadow-slate-900/10">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-purple-500/15 blur-3xl" />

        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge variant="brand" className="bg-brand-500/20 text-brand-300 border-brand-400/30 text-xs">
                Zero-Code Ingestion
              </Badge>
              <Badge variant="success" className="bg-emerald-500/20 text-emerald-300 border-emerald-400/30 text-xs">
                100% Deterministic Profiler
              </Badge>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Ingest, Audit &amp; Standardize Operational Data
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Accepts CSV, XLSX, or XLS files up to 25 MB. The profiler automatically computes missing value distributions, detects duplicate rows, and derives canonical schema candidates.
            </p>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end gap-2.5 w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-white/10">
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Air-Gapped Local Ingestion</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <Zap className="h-4 w-4 text-brand-400" />
              <span>Instant Schema Matcher</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Upload Dropzone Card */}
      <Card className="overflow-hidden border-slate-200/80 shadow-sm">
        <CardContent className="p-0">
          <div
            className={`relative border-2 border-dashed transition-all duration-300 ${
              isDragging
                ? 'border-brand-500 bg-brand-50/60 shadow-lg'
                : selectedFile
                ? 'border-slate-200 bg-slate-50/50'
                : 'border-slate-200 bg-white hover:border-brand-400 hover:bg-brand-50/20'
            }`}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={onInputChange}
              aria-label="Upload file"
            />

            <div className="p-8 sm:p-14">
              {!selectedFile ? (
                <div className="flex flex-col items-center justify-center text-center">
                  <div
                    className={`mb-6 flex h-20 w-20 items-center justify-center rounded-3xl transition-all duration-300 ${
                      isDragging
                        ? 'gradient-brand scale-110 shadow-xl shadow-brand-500/30 text-white'
                        : 'bg-brand-50 text-brand-600 border border-brand-100'
                    }`}
                  >
                    <UploadCloud className="h-10 w-10" />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 sm:text-2xl">
                    {isDragging ? 'Release to Ingest Dataset' : 'Drag & Drop Your Operational Spreadsheet'}
                  </h2>
                  <p className="mt-2 text-sm text-slate-500 max-w-md">
                    Works seamlessly with HR records, Sales journals, Financial ledgers, or custom ERP exports.
                  </p>
                  <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                    <Button
                      type="button"
                      size="lg"
                      onClick={() => inputRef.current?.click()}
                      className="bg-brand-600 hover:bg-brand-700 text-white font-bold shadow-md shadow-brand-500/25"
                    >
                      <UploadCloud className="mr-2 h-4 w-4" />
                      Browse Local Files
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="lg"
                      onClick={loadDemoData}
                    >
                      <Sparkles className="mr-2 h-4 w-4 text-brand-600" />
                      Load HR Demo File
                    </Button>
                  </div>

                  <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
                    {['CSV', 'XLSX', 'XLS'].map((fmt) => (
                      <span
                        key={fmt}
                        className="rounded-xl border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-600 shadow-2xs"
                      >
                        {fmt}
                      </span>
                    ))}
                    <span className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
                      Up to {MAX_FILE_SIZE_MB} MB
                    </span>
                  </div>
                </div>
              ) : (
                <div className="mx-auto max-w-xl space-y-6">
                  {/* File card */}
                  <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-md shadow-brand-500/20">
                      <FileSpreadsheet className="h-7 w-7" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-base font-bold text-slate-900">{selectedFile.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {formatBytes(selectedFile.size)} &bull;{' '}
                        {selectedFile.name.split('.').pop()?.toUpperCase() ?? 'FILE'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={resetUpload}
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-slate-400 transition hover:border-red-200 hover:bg-red-50 hover:text-red-500"
                      aria-label="Remove selected file"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Processing / Actions */}
                  <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                      <span>Ingestion Progress</span>
                      <span className="text-brand-600">
                        {uploadState === 'selected' && 'Ready for Deep Profiling'}
                        {uploadState === 'uploading' && 'Auditing & Computing Nulls...'}
                        {uploadState === 'success' && 'Ingestion & Audit Complete'}
                        {uploadState === 'error' && 'Ingestion Failed'}
                      </span>
                    </div>

                    <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          uploadState === 'success'
                            ? 'bg-emerald-500'
                            : uploadState === 'error'
                            ? 'bg-red-500'
                            : 'gradient-brand'
                        }`}
                        style={{ width: progressWidth }}
                      />
                    </div>

                    <div className="flex flex-wrap gap-3 pt-2">
                      <Button
                        type="button"
                        onClick={handleUpload}
                        disabled={uploadState === 'uploading' || uploadState === 'success'}
                        className="bg-brand-600 hover:bg-brand-700 text-white font-bold"
                      >
                        {uploadState === 'uploading' ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Ingesting &amp; Profiling...
                          </>
                        ) : uploadState === 'success' ? (
                          <>
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            Dataset Ready
                          </>
                        ) : (
                          <>
                            <Zap className="mr-2 h-4 w-4" />
                            Run Schema &amp; Data Audit
                          </>
                        )}
                      </Button>
                      <Button type="button" variant="secondary" onClick={resetUpload}>
                        Change File
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dataset Summary & Next Steps */}
      {datasetSummary && (
        <div className="space-y-6 animate-slide-up">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Deterministic Data Audit</h2>
              <p className="text-xs text-slate-500">Mathematical profiling completed natively across all dataset parameters.</p>
            </div>
            <Badge variant="success" dot>
              Audited &amp; Ready
            </Badge>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total Records" value={datasetSummary.rows?.toLocaleString() ?? 0} icon={Database} />
            <StatCard
              label="Schema Columns"
              value={datasetSummary.columns ?? 0}
              icon={FileSpreadsheet}
              iconClassName="bg-violet-50 text-violet-600"
            />
            <StatCard
              label="Missing Cells"
              value={datasetSummary.missing_cells?.toLocaleString() ?? 0}
              icon={AlertCircle}
              iconClassName="bg-amber-50 text-amber-600"
            />
            <StatCard
              label="Duplicate Records"
              value={datasetSummary.duplicate_rows ?? 0}
              icon={AlertCircle}
              iconClassName="bg-red-50 text-red-600"
            />
          </div>

          {/* Preview Table */}
          {datasetSummary.preview && datasetSummary.preview.length > 0 && (
            <Card className="overflow-hidden border-slate-200/80 shadow-sm">
              <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-3.5 flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-slate-800">Dataset Structure Preview</p>
                  <p className="text-xs text-slate-500">First 5 operational rows across identified fields</p>
                </div>
                <Badge variant="default" className="text-xs">
                  {Object.keys(datasetSummary.preview[0]).length} Detected Dimensions
                </Badge>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-100/70">
                      {Object.keys(datasetSummary.preview[0]).map((key) => (
                        <th
                          key={key}
                          className="whitespace-nowrap px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-slate-600"
                        >
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {datasetSummary.preview.slice(0, 5).map((row, index) => (
                      <tr
                        key={index}
                        className="border-b border-slate-100 odd:bg-white even:bg-slate-50/50 transition hover:bg-brand-50/30"
                      >
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="whitespace-nowrap px-4 py-2.5 text-xs text-slate-700">
                            {String(value ?? '—')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Next Step Call to Action */}
          <div className="rounded-3xl border border-brand-200 bg-gradient-to-r from-brand-50/80 via-white to-indigo-50/80 p-6 sm:p-8 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="brand" className="text-xs">Step 2 of 3</Badge>
                  <p className="text-lg font-bold text-slate-900">Proceed to Canonical Schema Mapping</p>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 max-w-xl">
                  Harmonize raw column headers with the canonical enterprise schema to unlock domain analytics,
                  automated KPI cards, and anomaly detection.
                </p>
              </div>
              <Button
                type="button"
                size="lg"
                className="bg-brand-600 hover:bg-brand-700 text-white font-bold shrink-0 shadow-md shadow-brand-500/25"
                onClick={() => {
                  if (!uploadId) return
                  navigate(`/mapping/${uploadId}`)
                }}
                disabled={!uploadId}
              >
                Review &amp; Map Columns
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 animate-slide-up">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div>
            <p className="font-semibold text-red-800">Dataset Ingestion Error</p>
            <p className="mt-1 text-xs text-red-700 leading-relaxed">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}
