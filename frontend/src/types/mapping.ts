export interface UploadResult {
  success: boolean
  upload_id: string
  filename: string
  file_type: string
  file_size: number
  status: string
  dataset: DatasetSummary | null
}

export interface DatasetSummary {
  rows?: number
  columns?: number
  missing_cells?: number
  duplicate_rows?: number
  preview?: Array<Record<string, unknown>>
  columns_meta?: Array<Record<string, unknown>>
}

export interface ColumnInfo {
  key: string
  label: string
  category: string
  type: string
  description: string
}

export interface MappingSuggestion {
  source: string
  normalized: string
  suggested_target: string | null
  confidence: number
  status: string
  reason: string
}

export interface MappingRow {
  source: string
  target: string
  ignored: boolean
  confidence: number
  status: string
  reason: string
  normalized: string
  method: string
  user_confirmed: boolean
}

export interface MappingValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  mapped_fields: Record<string, string>
}

export interface StandardizedDataset {
  success: boolean
  row_count: number
  column_count: number
  columns: string[]
  rows: Array<Record<string, unknown>>
  preview?: Array<Record<string, unknown>>
}
