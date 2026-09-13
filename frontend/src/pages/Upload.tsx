import { useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { StatCard } from '../components/ui/StatCard'
import api from '../services/api'

const MAX_FILE_SIZE_MB = 25

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 Bytes'
  const units = ['Bytes', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** index
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`
}

function UploadPage() {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadState, setUploadState] = useState<
    'idle' | 'selected' | 'uploading' | 'success' | 'error'
  >('idle')
  const [error, setError] = useState('')
  const [datasetSummary, setDatasetSummary] = useState<{
    rows?: number
    columns?: number
    missing_cells?: number
    duplicate_rows?: number
    preview?: Array<Record<string, unknown>>
  } | null>(null)

  const handleFileSelection = (file: File | null) => {
    if (!file) return

    const allowedTypes = ['csv', 'xlsx', 'xls']
    const extension = file.name.split('.').pop()?.toLowerCase() ?? ''

    if (!allowedTypes.includes(extension)) {
      setError('Unsupported file type. Please upload a CSV or Excel workbook.')
      setUploadState('error')
      return
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File is too large. Maximum allowed size is ${MAX_FILE_SIZE_MB} MB.`)
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

  const resetUpload = () => {
    setSelectedFile(null)
    setError('')
    setUploadState('idle')
    setDatasetSummary(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadState('uploading')
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await api.post('/api/v1/uploads', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setDatasetSummary(response.data.dataset ?? null)
      setUploadState('success')
    } catch (uploadError) {
      const message = uploadError instanceof Error ? uploadError.message : 'Upload failed.'
      setError(message)
      setUploadState('error')
    }
  }

  const progressWidth =
    uploadState === 'success' ? '100%' : uploadState === 'uploading' ? '66%' : '50%'

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Upload"
        title="Upload Business Data"
        description="Import your Excel or CSV file to begin AI-powered analysis and reporting."
      />

      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <div
            className={`relative border-2 border-dashed transition-all duration-300 ${
              isDragging
                ? 'border-brand-400 bg-brand-50/50 shadow-[var(--shadow-glow)]'
                : selectedFile
                  ? 'border-slate-200 bg-slate-50/50'
                  : 'border-slate-200 bg-white hover:border-brand-300 hover:bg-brand-50/20'
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

            <div className="p-6 sm:p-10">
              {!selectedFile ? (
                <div className="flex flex-col items-center justify-center text-center">
                  <div
                    className={`mb-6 flex h-20 w-20 items-center justify-center rounded-2xl transition-all duration-300 ${
                      isDragging
                        ? 'gradient-brand scale-110 shadow-lg shadow-brand-500/30'
                        : 'bg-brand-50 text-brand-600'
                    }`}
                  >
                    <UploadCloud className="h-10 w-10" />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 sm:text-2xl">
                    {isDragging ? 'Drop your file here' : 'Drag & drop your file'}
                  </h2>
                  <p className="mt-2 text-sm text-slate-500">or browse from your computer</p>
                  <Button
                    type="button"
                    className="mt-6"
                    size="lg"
                    onClick={() => inputRef.current?.click()}
                  >
                    <UploadCloud className="h-4 w-4" />
                    Browse files
                  </Button>
                  <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
                    {['XLSX', 'CSV', 'XLS'].map((fmt) => (
                      <span
                        key={fmt}
                        className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500"
                      >
                        {fmt}
                      </span>
                    ))}
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
                      Max {MAX_FILE_SIZE_MB} MB
                    </span>
                  </div>
                </div>
              ) : (
                <div className="mx-auto max-w-xl space-y-5">
                  <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                      <FileSpreadsheet className="h-7 w-7" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold text-slate-900">{selectedFile.name}</p>
                      <p className="text-sm text-slate-500">
                        {formatBytes(selectedFile.size)} &middot;{' '}
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

                  <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-slate-700">Upload progress</span>
                      <span className="text-slate-500">
                        {uploadState === 'selected' && 'Ready'}
                        {uploadState === 'uploading' && 'Processing...'}
                        {uploadState === 'success' && 'Complete'}
                        {uploadState === 'error' && 'Failed'}
                      </span>
                    </div>

                    <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          uploadState === 'success'
                            ? 'gradient-brand'
                            : uploadState === 'error'
                              ? 'bg-red-500'
                              : 'gradient-brand'
                        }`}
                        style={{ width: progressWidth }}
                      />
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <Button
                        type="button"
                        onClick={handleUpload}
                        disabled={uploadState === 'uploading' || uploadState === 'success'}
                      >
                        {uploadState === 'uploading' ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Processing...
                          </>
                        ) : uploadState === 'success' ? (
                          <>
                            <CheckCircle2 className="h-4 w-4" />
                            Done
                          </>
                        ) : (
                          'Process file'
                        )}
                      </Button>
                      <Button type="button" variant="secondary" onClick={resetUpload}>
                        Remove
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {datasetSummary && (
        <div className="space-y-6 animate-slide-up">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Dataset Summary</h2>
            <Badge variant="success" dot>
              Ready for analysis
            </Badge>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Rows" value={datasetSummary.rows ?? 0} icon={FileSpreadsheet} />
            <StatCard
              label="Columns"
              value={datasetSummary.columns ?? 0}
              icon={FileSpreadsheet}
              iconClassName="bg-violet-50 text-violet-600"
            />
            <StatCard
              label="Missing Cells"
              value={datasetSummary.missing_cells ?? 0}
              icon={AlertCircle}
              iconClassName="bg-amber-50 text-amber-600"
            />
            <StatCard
              label="Duplicates"
              value={datasetSummary.duplicate_rows ?? 0}
              icon={AlertCircle}
              iconClassName="bg-red-50 text-red-600"
            />
          </div>

          {datasetSummary.preview && datasetSummary.preview.length > 0 && (
            <Card className="overflow-hidden">
              <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-3">
                <p className="text-sm font-semibold text-slate-700">Data Preview</p>
                <p className="text-xs text-slate-500">First 5 rows</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/50">
                      {Object.keys(datasetSummary.preview[0]).map((key) => (
                        <th
                          key={key}
                          className="whitespace-nowrap px-5 py-3 text-xs font-bold uppercase tracking-wider text-slate-500"
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
                        className="border-b border-slate-50 transition hover:bg-brand-50/20"
                      >
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="whitespace-nowrap px-5 py-3 text-slate-600">
                            {String(value ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 animate-slide-up">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div>
            <p className="font-semibold text-red-800">Unable to process file</p>
            <p className="mt-1 text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default UploadPage
